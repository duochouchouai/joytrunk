/**
 * WebSocket /ws/im：官网 IM 客户端长连，接收实时推送（含 JoyTrunk 回复）
 * 鉴权：首帧 { type: 'auth', token } 或 Cookie；解析出 user_id 后加入 userIdToImWs
 */
const { WebSocketServer } = require('ws');
const jwt = require('jsonwebtoken');
const config = require('../config/default');

const IM_WS_PATH = '/ws/im';

/** user_id -> Set<WebSocket> */
const userIdToImWs = new Map();

function getImWsSetByUserId(userId) {
  const uid = Number(userId);
  if (!userIdToImWs.has(uid)) userIdToImWs.set(uid, new Set());
  return userIdToImWs.get(uid);
}

function broadcastToUser(userId, data) {
  const set = userIdToImWs.get(Number(userId));
  const count = set ? set.size : 0;
  if (process.env.DEBUG_WS === '1' || (process.env.JOYTRUNK_DEBUG || '').toLowerCase().includes('ws')) {
    console.log('[ws/im] broadcastToUser', 'user_id=', userId, 'sockets=', count, 'type=', data && data.type);
  }
  if (!set) return;
  const payload = typeof data === 'string' ? data : JSON.stringify(data);
  for (const ws of set) {
    if (ws.readyState === 1) {
      try {
        ws.send(payload);
      } catch (_) {}
    }
  }
}

function attachImWs(server) {
  const wss = new WebSocketServer({ noServer: true });

  wss.on('connection', (ws, request) => {
    let userId = null;

    ws.on('message', (data) => {
      if (userId != null) return; // 已鉴权，忽略后续
      try {
        const msg = JSON.parse(data.toString());
        if (msg.type !== 'auth') return;
        const token = msg.token || msg.jwt;
        if (!token) {
          ws.close(4003, 'auth required');
          return;
        }
        let uid = null;
        if (typeof token === 'string' && token.length > 50 && token.includes('.')) {
          const decoded = jwt.verify(token, config.JWT_SECRET, { algorithms: [config.JWT_ALGORITHM] });
          uid = decoded.sub != null ? decoded.sub : decoded.userId;
        } else if (config.ALLOW_X_OWNER_ID_FALLBACK && /^\d+$/.test(String(token).trim())) {
          uid = Number(String(token).trim());
        }
        if (uid == null) {
          ws.close(4003, 'invalid token');
          return;
        }
        userId = Number(uid);
        const set = getImWsSetByUserId(userId);
        set.add(ws);
        if (process.env.DEBUG_WS === '1' || (process.env.JOYTRUNK_DEBUG || '').toLowerCase().includes('ws')) {
          console.log('[ws/im] auth_ok user_id=', userId);
        }
        ws.send(JSON.stringify({ type: 'auth_ok' }));
      } catch (e) {
        ws.close(4003, 'auth failed');
      }
    });

    ws.on('close', () => {
      if (userId != null) {
        const set = userIdToImWs.get(userId);
        if (set) {
          set.delete(ws);
          if (set.size === 0) userIdToImWs.delete(userId);
        }
      }
    });
    ws.on('error', () => {
      if (userId != null) {
        const set = userIdToImWs.get(userId);
        if (set) {
          set.delete(ws);
          if (set.size === 0) userIdToImWs.delete(userId);
        }
      }
    });
  });

  function handleUpgrade(request, socket, head) {
    wss.handleUpgrade(request, socket, head, (ws) => {
      wss.emit('connection', ws, request);
    });
  }

  return { path: IM_WS_PATH, handleUpgrade };
}

module.exports = { attachImWs, broadcastToUser, IM_WS_PATH };
