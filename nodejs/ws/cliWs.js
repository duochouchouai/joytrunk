/**
 * WebSocket /ws/cli：CLI 长连，鉴权（api_key -> user_id）、心跳、单用户单连接
 * 供 server.js 在 upgrade 时调用。
 */
const { WebSocketServer } = require('ws');
const { getDb } = require('../db/pg');
const { userIdToCliWs, getCliWsByUserId } = require('./cliState');
const { broadcastToUser } = require('./imWs');

const CLI_WS_PATH = '/ws/cli';
const HEARTBEAT_IDLE_MS = 90 * 1000; // 90s 无消息则关闭

function attachCliWs(server) {
  const wss = new WebSocketServer({ noServer: true });

  wss.on('connection', (ws, request) => {
    let userId = null;
    let heartbeatTimer = null;

    function clearHeartbeat() {
      if (heartbeatTimer) {
        clearTimeout(heartbeatTimer);
        heartbeatTimer = null;
      }
    }

    function scheduleHeartbeat() {
      clearHeartbeat();
      heartbeatTimer = setTimeout(() => {
        try {
          ws.close(4000, 'heartbeat timeout');
        } catch (_) {}
      }, HEARTBEAT_IDLE_MS);
    }

    function handleMessage(data) {
      scheduleHeartbeat();
      try {
        const msg = JSON.parse(data.toString());
        if (userId == null) {
          if (msg.type === 'auth' && msg.api_key) {
            getDb()
              .query('SELECT id FROM users WHERE joytrunk_api_key = $1 AND deleted_at IS NULL', [String(msg.api_key).trim()])
              .then((res) => {
                const row = res.rows[0];
                if (!row) {
                  ws.send(JSON.stringify({ type: 'auth_error', error: 'invalid api_key' }));
                  ws.close(4003, 'auth failed');
                  return;
                }
                const uid = Number(row.id);
                const old = userIdToCliWs.get(uid);
                if (old && old !== ws) {
                  try {
                    old.close(4002, 'replaced by new connection');
                  } catch (_) {}
                }
                userIdToCliWs.set(uid, ws);
                userId = uid;
                ws.send(JSON.stringify({ type: 'auth_ok' }));
                const pendingCliTasks = require('../services/pendingCliTasks');
                pendingCliTasks.getPendingTasks(uid).then((rows) => {
                  rows.forEach(({ task_id, payload }) => {
                    try {
                      ws.send(JSON.stringify({ type: 'task', task_id, ...payload }));
                    } catch (_) {}
                  });
                  return pendingCliTasks.deleteAllPendingForUser(uid);
                }).catch((err) => console.error('CLI send pending tasks', err));
              })
              .catch((err) => {
                console.error('CLI WS auth db error', err);
                ws.send(JSON.stringify({ type: 'auth_error', error: 'server error' }));
                ws.close(5000);
              });
          } else {
            ws.send(JSON.stringify({ type: 'auth_error', error: 'send auth first' }));
            ws.close(4003);
          }
          return;
        }
        if (msg.type === 'ping') {
          ws.send(JSON.stringify({ type: 'pong', ts: msg.ts }));
          return;
        }
        if (msg.type === 'task_result' && userId != null) {
          const taskId = msg.task_id;
          const status = msg.status;
          const content = msg.content || '';
          const error = msg.error;
          const conversationId = msg.conversation_id || msg.chat_id;
          broadcastToUser(userId, {
            type: 'joytrunk_reply',
            task_id: taskId,
            status,
            content,
            error: error || null,
            conversation_id: conversationId,
          });
          if (conversationId && status === 'completed') {
            const imService = require('../services/im');
            imService.insertJoytrunkReply(userId, conversationId, content).catch((e) => console.error('insertJoytrunkReply', e));
          }
          return;
        }
      } catch (_) {
        // ignore parse error
      }
    }

    ws.on('message', handleMessage);
    ws.on('close', () => {
      clearHeartbeat();
      if (userId != null && userIdToCliWs.get(userId) === ws) {
        userIdToCliWs.delete(userId);
      }
    });
    ws.on('error', () => {
      clearHeartbeat();
      if (userId != null && userIdToCliWs.get(userId) === ws) {
        userIdToCliWs.delete(userId);
      }
    });
  });

  function handleUpgrade(request, socket, head) {
    wss.handleUpgrade(request, socket, head, (ws) => {
      wss.emit('connection', ws, request);
    });
  }

  return { path: CLI_WS_PATH, handleUpgrade };
}

module.exports = { attachCliWs, getCliWsByUserId, CLI_WS_PATH };
