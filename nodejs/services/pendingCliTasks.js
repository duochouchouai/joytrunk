/**
 * 待下发给 CLI 的任务：入队、拉取、推送到 WebSocket 后删除
 */
const { getDb } = require('../db/pg');
const { getCliWsByUserId } = require('../ws/cliState');

async function enqueueTask(userId, taskId, payload) {
  const pool = getDb();
  await pool.query(
    'INSERT INTO pending_cli_tasks (user_id, task_id, payload) VALUES ($1, $2, $3)',
    [Number(userId), taskId, JSON.stringify(payload)]
  );
}

async function getPendingTasks(userId) {
  const pool = getDb();
  const result = await pool.query(
    'SELECT task_id, payload FROM pending_cli_tasks WHERE user_id = $1 ORDER BY id',
    [Number(userId)]
  );
  return (result.rows || []).map((r) => ({ task_id: r.task_id, payload: r.payload }));
}

async function deletePendingTask(userId, taskId) {
  const pool = getDb();
  await pool.query('DELETE FROM pending_cli_tasks WHERE user_id = $1 AND task_id = $2', [Number(userId), taskId]);
}

async function deleteAllPendingForUser(userId) {
  const pool = getDb();
  await pool.query('DELETE FROM pending_cli_tasks WHERE user_id = $1', [Number(userId)]);
}

/**
 * 若 CLI 在线则推送并从未决中删除；否则仅入队
 */
function pushOrEnqueueTask(userId, taskId, payload) {
  const ws = getCliWsByUserId(userId);
  if (ws && ws.readyState === 1) {
    try {
      ws.send(JSON.stringify({ type: 'task', task_id: taskId, ...payload }));
      return Promise.resolve(); // 已推送，不入队
    } catch (e) {
      // 推送失败则入队
    }
  }
  return enqueueTask(userId, taskId, payload);
}

module.exports = {
  enqueueTask,
  getPendingTasks,
  deletePendingTask,
  deleteAllPendingForUser,
  pushOrEnqueueTask,
};
