/**
 * JoyTrunk 官方后端：注册用户、IM、LLM Router（与本地 32890 gateway 解耦）
 * Phase 1：PostgreSQL + JWT + 1:1 会话与消息
 * 架构：路由层 → 控制层 → 服务层
 */
require('dotenv').config();
const http = require('http');
const path = require('path');
const fs = require('fs');
const express = require('express');
const cors = require('cors');
const config = require('./config/default');
const { getDb, isDbAvailable, initDb } = require('./db/pg');
const { initRedis } = require('./db/redis');
const { generateUid } = require('./utils/snowflake');
const { authMiddleware } = require('./middleware/auth');
const authRoutes = require('./routes/auth');
const userRoutes = require('./routes/user');
const imRoutes = require('./routes/im');
const cliBindRoutes = require('./routes/cliBind');
const { attachCliWs } = require('./ws/cliWs');
const { attachImWs } = require('./ws/imWs');

const app = express();
const PORT = config.PORT;
const HOST = config.HOST;

// 若已构建前端（vue/dist 存在），则根路径由前端托管
const frontendDist = path.join(__dirname, '../vue/dist');
const serveFrontend = fs.existsSync(frontendDist);

// CORS：显式允许前端开发源，避免预检/错误响应缺头
const allowedOrigins = [
  'http://localhost:32892',
  'http://127.0.0.1:32892',
  'http://localhost:32891',
  'http://127.0.0.1:32891',
];
app.use(
  cors({
    origin: (origin, cb) => {
      if (!origin || allowedOrigins.includes(origin)) return cb(null, true);
      cb(null, false);
    },
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Owner-Id'],
    optionsSuccessStatus: 200,
  })
);
app.use(express.json());

app.get('/api/health', (req, res) => {
  res.json({
    ok: true,
    service: 'joytrunk-official',
    message: 'JoyTrunk 官方后端（注册用户、IM）',
    port: PORT,
  });
});

if (!serveFrontend) {
  app.get('/', (req, res) => {
    res.json({
      service: 'JoyTrunk 官方后端',
      docs: '本地管理请使用 joytrunk server 启动 cli 内 server，访问 http://localhost:32890',
    });
  });
}

app.use('/api/auth', authRoutes);
app.use('/api/users', authMiddleware, userRoutes);
app.use('/api/im', authMiddleware, imRoutes);
app.use('/api/cli', cliBindRoutes);

app.use((err, req, res, next) => {
  const origin = req.get('Origin');
  if (origin && allowedOrigins.includes(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Access-Control-Allow-Credentials', 'true');
  }
  if (err && err.code === 'REDIS_UNAVAILABLE') {
    return res.status(503).json({
      error: '服务暂不可用',
      code: 'REDIS_UNAVAILABLE',
    });
  }
  if (err && (err.code === 'DB_UNAVAILABLE' || (err.message && err.message.includes('DB_UNAVAILABLE')))) {
    return res.status(503).json({
      error: '数据库连接失败，请检查 PostgreSQL 配置（.env 中 DATABASE_URL 或 PG_*）',
      code: 'DB_UNAVAILABLE',
    });
  }
  next(err);
});

app.use((err, req, res, next) => {
  const origin = req.get('Origin');
  if (origin && allowedOrigins.includes(origin)) {
    res.setHeader('Access-Control-Allow-Origin', origin);
    res.setHeader('Access-Control-Allow-Credentials', 'true');
  }
  if (res.headersSent) return next(err);
  console.error('Unhandled error:', err);
  res.status(500).json({ error: 'Internal Server Error' });
});

// 托管前端静态（需先在 vue 目录执行 npm run build）
if (serveFrontend) {
  app.use(express.static(frontendDist));
  app.get('*', (req, res) => res.sendFile(path.join(frontendDist, 'index.html')));
}

async function seedIfEmpty() {
  const pool = getDb();
  const result = await pool.query('SELECT COUNT(*) AS n FROM users');
  const count = parseInt(result.rows[0]?.n || '0', 10);
  if (count > 0) return;
  const uid1 = generateUid();
  const uid2 = generateUid();
  const uid3 = generateUid();
  await pool.query(
    "INSERT INTO users (type, name, phone, uid) VALUES ('user', '测试用户A', '13800000001', $1), ('user', '测试用户B', '13800000002', $2), ('user', '测试用户C', '13800000003', $3)",
    [uid1, uid2, uid3]
  );
}

if (require.main === module) {
  (async () => {
    await initDb();
    await initRedis();
    await seedIfEmpty();
    const server = http.createServer(app);
    const cliWs = attachCliWs(server);
    const imWs = attachImWs(server);
    server.on('upgrade', (request, socket, head) => {
      const urlPath = request.url?.split('?')[0] || '';
      if (urlPath === cliWs.path) return cliWs.handleUpgrade(request, socket, head);
      if (urlPath === imWs.path) return imWs.handleUpgrade(request, socket, head);
      socket.destroy();
    });
    server.listen(PORT, HOST, () => {
      console.log(`JoyTrunk official backend on http://${HOST}:${PORT}`);
      if (serveFrontend) console.log('Frontend (vue/dist) is served at /');
    });
  })().catch((e) => {
    console.error('Startup failed:', e);
    process.exit(1);
  });
}

module.exports = { app, PORT, HOST, getDb, seedIfEmpty, isDbAvailable };
