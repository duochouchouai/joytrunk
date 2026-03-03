/**
 * 排查「A 给 B 发消息，B 看不到」：检查 participants 是否含 B，以及 B 的会话列表。
 * 用法：node scripts/debug-im-visibility.js
 * 依赖：.env 中 DATABASE_URL 或 PG_*，且已有测试用户（npm run seed 或 server 的 seedIfEmpty）。
 */
require('dotenv').config();
const { initDb, getDb } = require('../db/pg');
const imService = require('../services/im');

async function main() {
  await initDb();
  const pool = getDb();

  const userResult = await pool.query(
    "SELECT id, name, email FROM users WHERE email IN ('test1@test.local', 'test2@test.local') ORDER BY id"
  );
  let users = userResult.rows || [];
  if (users.length < 2) {
    const anyTwo = await pool.query('SELECT id, name, email FROM users ORDER BY id LIMIT 2');
    users = anyTwo.rows || [];
  }
  if (users.length < 2) {
    console.log('需要至少两名用户。请先执行: npm run seed 或启动 server 触发 seedIfEmpty');
    process.exitCode = 1;
    return;
  }
  const userA = users[0];
  const userB = users[1];
  const idA = userA.id;
  const idB = userB.id;
  console.log('用户 A:', userA.id, userA.name, userA.email);
  console.log('用户 B:', userB.id, userB.name, userB.email);

  const createResult = await imService.findOrCreateDirectConversation(idA, idB);
  if (createResult.error) {
    console.error('创建会话失败:', createResult.error);
    process.exitCode = 1;
    return;
  }
  const convId = createResult.conversationId;
  console.log('会话 id:', convId);

  const participantsResult = await pool.query(
    'SELECT conversation_id, user_id, role FROM participants WHERE conversation_id = $1 ORDER BY user_id',
    [convId]
  );
  const participants = participantsResult.rows || [];
  console.log('participants 行数:', participants.length);
  participants.forEach((p) => console.log('  ', p.user_id, p.role));
  if (participants.length !== 2) {
    console.error('预期 2 条 participants，当前为', participants.length, '→ B 无法看到会话');
  } else {
    const hasB = participants.some((p) => Number(p.user_id) === Number(idB));
    if (!hasB) console.error('participants 中缺少 B (user_id=' + idB + ')');
  }

  const sendResult = await imService.sendMessage(convId, idA, 'hello from A');
  if (sendResult.error) {
    console.error('A 发消息失败:', sendResult.error);
  } else {
    console.log('A 已发送消息:', sendResult.message?.content);
  }

  const listForB = await imService.getConversationsForUser(idB);
  console.log('B 的会话列表条数:', listForB.length);
  listForB.forEach((c) => console.log('  ', c.id, c.title, c.last_message?.content));
  const bSeesConv = listForB.some((c) => c.id === convId);
  if (!bSeesConv) {
    console.error('B 的列表中未包含该会话 → 请检查 participants 是否含 B');
  } else {
    console.log('OK: B 能看到该会话');
  }
}

main().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
