/**
 * 种子脚本：创建两名测试用户（邮箱 + 密码登录）
 * 幂等：已存在则更新密码与昵称。
 * 用法：npm run seed 或 node scripts/seed-test-users.js
 */
require('dotenv').config();
const bcrypt = require('bcryptjs');
const { initDb, getDb } = require('../db/pg');
const { generateUid } = require('../utils/snowflake');

const SALT_ROUNDS = 10;

const TEST_USERS = [
  { email: 'test1@test.local', password: 'test123456', name: '测试用户A' },
  { email: 'test2@test.local', password: 'test123456', name: '测试用户B' },
];

async function seed() {
  await initDb();
  const pool = getDb();
  for (const u of TEST_USERS) {
    const hash = bcrypt.hashSync(u.password, SALT_ROUNDS);
    const uid = generateUid();
    await pool.query(
      `INSERT INTO users (type, name, email, password_hash, uid)
       VALUES ('user', $1, $2, $3, $4)
       ON CONFLICT (email) DO UPDATE SET
         name = EXCLUDED.name,
         password_hash = EXCLUDED.password_hash,
         updated_at = CURRENT_TIMESTAMP`,
      [u.name, u.email, hash, uid]
    );
    console.log('OK:', u.email, u.name);
  }
  console.log('测试用户已就绪，可用账号密码登录：');
  TEST_USERS.forEach((u) => console.log('  ', u.email, ' / ', u.password));
}

seed().catch((e) => {
  console.error('seed failed:', e.message || e);
  process.exitCode = 1;
});
