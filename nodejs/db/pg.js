/**
 * PostgreSQL 连接与建表（users, conversations, participants, messages, user_conversation_status）
 * 配置由 .env 提供，经 config/default.js 暴露。建表与迁移幂等。
 */
const { Pool } = require('pg');
const config = require('../config/default');
const { generateUid } = require('../utils/snowflake');

const SCHEMA_SQL = `
  CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    type TEXT NOT NULL CHECK (type IN ('user','official','agent')),
    name TEXT NOT NULL,
    avatar_url TEXT,
    balance INTEGER NOT NULL DEFAULT 0,
    phone TEXT UNIQUE,
    email TEXT UNIQUE,
    wechat_open_id TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
  );
  CREATE TABLE IF NOT EXISTS conversations (
    id SERIAL PRIMARY KEY,
    type TEXT NOT NULL CHECK (type IN ('direct','official','group')),
    title TEXT,
    peer_ids TEXT,
    creator_id INTEGER REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(peer_ids)
  );
  CREATE TABLE IF NOT EXISTS participants (
    conversation_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('owner','admin','member')),
    joined_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (conversation_id, user_id),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
  );
  CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    sender_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'sent' CHECK (status IN ('sent','delivered','read')),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    FOREIGN KEY (sender_id) REFERENCES users(id)
  );
  CREATE TABLE IF NOT EXISTS user_conversation_status (
    user_id INTEGER NOT NULL,
    conversation_id INTEGER NOT NULL,
    last_read_msg_id INTEGER,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, conversation_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
  );
  CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);
  CREATE INDEX IF NOT EXISTS idx_messages_conversation_created ON messages(conversation_id, created_at DESC);
  CREATE INDEX IF NOT EXISTS idx_participants_conversation ON participants(conversation_id);
  CREATE INDEX IF NOT EXISTS idx_participants_user ON participants(user_id);
`;

function getPoolConfig() {
  if (config.DATABASE_URL) {
    const opts = { connectionString: config.DATABASE_URL };
    if (config.PG_POOL_MAX != null) opts.max = Number(config.PG_POOL_MAX);
    if (config.PG_POOL_IDLE_TIMEOUT_MILLIS != null) opts.idleTimeoutMillis = Number(config.PG_POOL_IDLE_TIMEOUT_MILLIS);
    if (config.PG_POOL_CONNECTION_TIMEOUT_MILLIS != null) opts.connectionTimeoutMillis = Number(config.PG_POOL_CONNECTION_TIMEOUT_MILLIS);
    if (config.PG_SSL === true || config.PG_SSL === 'true') {
      opts.ssl = { rejectUnauthorized: false };
    }
    return opts;
  }
  const opts = {
    host: config.PG_HOST || 'localhost',
    port: Number(config.PG_PORT) || 5432,
    user: config.PG_USER || 'postgres',
    password: config.PG_PASSWORD || '',
    database: config.PG_DATABASE || 'joytrunk',
    max: Number(config.PG_POOL_MAX) || 10,
    idleTimeoutMillis: Number(config.PG_POOL_IDLE_TIMEOUT_MILLIS) || 10000,
    connectionTimeoutMillis: Number(config.PG_POOL_CONNECTION_TIMEOUT_MILLIS) || 5000,
  };
  if (config.PG_SSL === true || config.PG_SSL === 'true') {
    opts.ssl = { rejectUnauthorized: false };
  }
  return opts;
}

/** 从配置中解析目标数据库名 */
function getTargetDatabaseName() {
  if (config.DATABASE_URL) {
    const match = config.DATABASE_URL.match(/\/([^/?]+)(\?|$)/);
    return (match && match[1]) ? decodeURIComponent(match[1]) : 'joytrunk';
  }
  return config.PG_DATABASE || 'joytrunk';
}

/** 若目标数据库不存在则创建（连接 postgres 默认库执行 CREATE DATABASE） */
async function ensureDatabaseExists() {
  const dbName = getTargetDatabaseName();
  let adminPool;
  if (config.DATABASE_URL) {
    const adminUrl = config.DATABASE_URL.replace(/\/([^/?]+)(\?|$)/, '/postgres$2');
    const opts = { connectionString: adminUrl };
    if (config.PG_SSL || (config.DATABASE_URL && config.DATABASE_URL.includes('sslmode='))) {
      opts.ssl = { rejectUnauthorized: false };
    }
    adminPool = new Pool(opts);
  } else {
    adminPool = new Pool({
      host: config.PG_HOST || 'localhost',
      port: Number(config.PG_PORT) || 5432,
      user: config.PG_USER || 'postgres',
      password: config.PG_PASSWORD || '',
      database: 'postgres',
      ssl: config.PG_SSL ? { rejectUnauthorized: false } : undefined,
    });
  }
  const client = await adminPool.connect();
  try {
    const res = await client.query('SELECT 1 FROM pg_database WHERE datname = $1', [dbName]);
    if (!res.rows || res.rows.length === 0) {
      await client.query(`CREATE DATABASE "${dbName.replace(/"/g, '""')}" ENCODING 'UTF8'`);
    }
  } finally {
    client.release();
    await adminPool.end();
  }
}

async function runMigrations(pool) {
  const client = await pool.connect();
  try {
    const res = await client.query(
      `SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'users'`
    );
    const columns = (res.rows || []).map((r) => r.column_name);
    if (!columns.includes('password_hash')) {
      await client.query('ALTER TABLE users ADD COLUMN password_hash TEXT');
    }
    if (!columns.includes('deleted_at')) {
      await client.query('ALTER TABLE users ADD COLUMN deleted_at TIMESTAMPTZ');
    }
    if (!columns.includes('uid')) {
      await client.query('ALTER TABLE users ADD COLUMN uid BIGINT UNIQUE');
      const rows = await client.query('SELECT id FROM users WHERE uid IS NULL');
      for (const row of rows.rows || []) {
        const uid = generateUid();
        await client.query('UPDATE users SET uid = $1 WHERE id = $2', [uid, row.id]);
      }
      await client.query('ALTER TABLE users ALTER COLUMN uid SET NOT NULL');
    }
    // IM 索引与 user_conversation_status 扩展（技术落地补充）
    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages (conversation_id, id)
    `);
    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_messages_conv_sender_status ON messages (conversation_id, sender_id, status) WHERE is_deleted = 0
    `);
    const ucsColumns = await client.query(
      `SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'user_conversation_status'`
    );
    const ucsCols = (ucsColumns.rows || []).map((r) => r.column_name);
    if (!ucsCols.includes('pinned_at')) {
      await client.query('ALTER TABLE user_conversation_status ADD COLUMN pinned_at TIMESTAMPTZ');
    }
    if (!ucsCols.includes('deleted_at')) {
      await client.query('ALTER TABLE user_conversation_status ADD COLUMN deleted_at TIMESTAMPTZ');
    }
    await client.query(`
      CREATE INDEX IF NOT EXISTS idx_ucs_user_pinned_updated ON user_conversation_status (user_id, pinned_at DESC NULLS LAST, updated_at DESC)
    `);
    const convColumns = await client.query(
      `SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'conversations'`
    );
    const convCols = (convColumns.rows || []).map((r) => r.column_name);
    if (!convCols.includes('dismissed_at')) {
      await client.query('ALTER TABLE conversations ADD COLUMN dismissed_at TIMESTAMPTZ');
    }
    if (!convCols.includes('avatar_url')) {
      await client.query('ALTER TABLE conversations ADD COLUMN avatar_url TEXT');
    }
    if (!convCols.includes('announcement')) {
      await client.query('ALTER TABLE conversations ADD COLUMN announcement TEXT');
    }
    if (!convCols.includes('announcement_updated_at')) {
      await client.query('ALTER TABLE conversations ADD COLUMN announcement_updated_at TIMESTAMPTZ');
    }
    if (!convCols.includes('joytrunk_conversation')) {
      await client.query('ALTER TABLE conversations ADD COLUMN joytrunk_conversation BOOLEAN DEFAULT false');
    }
    if (!convCols.includes('joytrunk_employee_id')) {
      await client.query('ALTER TABLE conversations ADD COLUMN joytrunk_employee_id TEXT');
    }
    await client.query(`
      CREATE TABLE IF NOT EXISTS pending_cli_tasks (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        task_id TEXT NOT NULL,
        payload JSONB NOT NULL,
        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
      )
    `);
    await client.query('CREATE INDEX IF NOT EXISTS idx_pending_cli_tasks_user_id ON pending_cli_tasks (user_id)');
    const partColumns = await client.query(
      `SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'participants'`
    );
    const partCols = (partColumns.rows || []).map((r) => r.column_name);
    if (!partCols.includes('muted_until')) {
      await client.query('ALTER TABLE participants ADD COLUMN muted_until TIMESTAMPTZ');
    }
    const msgColumns = await client.query(
      `SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'messages'`
    );
    const msgCols = (msgColumns.rows || []).map((r) => r.column_name);
    if (!msgCols.includes('mention_user_ids')) {
      await client.query('ALTER TABLE messages ADD COLUMN mention_user_ids INTEGER[]');
    }
    if (!msgCols.includes('image_url')) {
      await client.query('ALTER TABLE messages ADD COLUMN image_url TEXT');
    }
    if (!columns.includes('joytrunk_api_key')) {
      await client.query('ALTER TABLE users ADD COLUMN joytrunk_api_key TEXT');
    }
    if (!columns.includes('sync_joytrunk_chat')) {
      await client.query('ALTER TABLE users ADD COLUMN sync_joytrunk_chat BOOLEAN DEFAULT true');
    }
    await client.query(`
      CREATE TABLE IF NOT EXISTS user_cli_employees (
        user_id INTEGER NOT NULL REFERENCES users(id),
        employee_id TEXT NOT NULL,
        name TEXT NOT NULL DEFAULT '',
        synced_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, employee_id)
      )
    `);
    await client.query('CREATE INDEX IF NOT EXISTS idx_user_cli_employees_user_id ON user_cli_employees (user_id)');
    const joytrunkBot = await client.query('SELECT id FROM users WHERE uid = 0');
    if (!joytrunkBot.rows[0]) {
      await client.query(
        "INSERT INTO users (type, name, uid) SELECT 'agent', 'JoyTrunk', 0 WHERE NOT EXISTS (SELECT 1 FROM users WHERE uid = 0)"
      );
    }
    await client.query(`
      CREATE TABLE IF NOT EXISTS llm_usage (
        id BIGSERIAL PRIMARY KEY,
        uid BIGINT NOT NULL,
        source VARCHAR(32) NOT NULL DEFAULT 'router',
        model VARCHAR(128),
        prompt_tokens INT NOT NULL DEFAULT 0,
        completion_tokens INT NOT NULL DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
      )
    `);
    await client.query('CREATE INDEX IF NOT EXISTS idx_llm_usage_uid_created ON llm_usage (uid, created_at DESC)');
  } finally {
    client.release();
  }
}

let poolInstance = null;

function getDb() {
  if (!poolInstance) {
    const e = new Error('DB_UNAVAILABLE');
    e.code = 'DB_UNAVAILABLE';
    throw e;
  }
  return poolInstance;
}

function isDbAvailable() {
  return poolInstance != null;
}

async function initDb() {
  if (poolInstance) return;
  try {
    await ensureDatabaseExists();
    const poolConfig = getPoolConfig();
    const pool = new Pool(poolConfig);
    const client = await pool.connect();
    try {
      const statements = SCHEMA_SQL.split(';').filter((s) => s.trim());
      for (const stmt of statements) {
        if (stmt.trim()) await client.query(stmt + ';');
      }
      await runMigrations(pool);
    } finally {
      client.release();
    }
    poolInstance = pool;
  } catch (e) {
    console.error('PostgreSQL initDb failed:', e.code || '', e.message);
    const err = new Error('DB_UNAVAILABLE');
    err.code = 'DB_UNAVAILABLE';
    err.cause = e;
    throw err;
  }
}

function setDbInstance(instance) {
  poolInstance = instance;
}

module.exports = {
  getDb,
  isDbAvailable,
  initDb,
  setDbInstance,
};
