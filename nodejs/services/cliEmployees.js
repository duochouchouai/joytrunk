/**
 * CLI 同步的员工列表：按 user_id 存储，供 IM 获取并选择员工下发任务
 */
const { getDb } = require('../db/pg');

/**
 * 保存该用户的 CLI 员工列表（全量替换）
 * @param {number} userId - users.id
 * @param {{ id: string, name: string }[]} employees
 */
async function saveCliEmployees(userId, employees) {
  if (userId == null) return;
  const pool = getDb();
  const list = Array.isArray(employees) ? employees : [];
  const client = await pool.connect();
  try {
    await client.query('DELETE FROM user_cli_employees WHERE user_id = $1', [Number(userId)]);
    const now = new Date().toISOString();
    for (const e of list) {
      const id = (e && (e.id ?? e.employee_id)) != null ? String(e.id || e.employee_id).trim() : '';
      const name = (e && e.name) != null ? String(e.name).trim() : '';
      if (!id) continue;
      await client.query(
        'INSERT INTO user_cli_employees (user_id, employee_id, name, synced_at) VALUES ($1, $2, $3, $4) ON CONFLICT (user_id, employee_id) DO UPDATE SET name = $3, synced_at = $4',
        [Number(userId), id, name, now]
      );
    }
  } finally {
    client.release();
  }
}

/**
 * 获取该用户已同步的 CLI 员工列表
 * @param {number} userId - users.id
 * @returns {{ id: string, name: string }[]}
 */
async function getCliEmployees(userId) {
  if (userId == null) return [];
  const pool = getDb();
  const result = await pool.query(
    'SELECT employee_id, name FROM user_cli_employees WHERE user_id = $1 ORDER BY employee_id',
    [Number(userId)]
  );
  return (result.rows || []).map((r) => ({ id: r.employee_id, name: r.name || '' }));
}

module.exports = { saveCliEmployees, getCliEmployees };
