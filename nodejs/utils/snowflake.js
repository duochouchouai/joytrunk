/**
 * 雪花算法：生成 64 位唯一 ID，用于用户 uid。
 * 布局：1 位符号 + 41 位时间戳(ms) + 5 位 datacenter + 5 位 worker + 12 位序列。
 * 返回字符串避免 JS Number 精度问题，便于 JSON 与前端使用。
 */
const config = require('../config/default');

const EPOCH = 1609459200000; // 2021-01-01 00:00:00 UTC
const WORKER_BITS = 5;
const DATACENTER_BITS = 5;
const SEQUENCE_BITS = 12;

const MAX_WORKER = (1 << WORKER_BITS) - 1;
const MAX_DATACENTER = (1 << DATACENTER_BITS) - 1;
const MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1;

const WORKER_SHIFT = SEQUENCE_BITS;
const DATACENTER_SHIFT = SEQUENCE_BITS + WORKER_BITS;
const TIMESTAMP_SHIFT = SEQUENCE_BITS + WORKER_BITS + DATACENTER_BITS;

let lastTimestamp = -1;
let sequence = 0;

function getWorkerId() {
  const id = config.SNOWFLAKE_WORKER_ID != null ? Number(config.SNOWFLAKE_WORKER_ID) : 0;
  return Math.max(0, Math.min(MAX_WORKER, Math.floor(id)));
}

function getDatacenterId() {
  const id = config.SNOWFLAKE_DATACENTER_ID != null ? Number(config.SNOWFLAKE_DATACENTER_ID) : 0;
  return Math.max(0, Math.min(MAX_DATACENTER, Math.floor(id)));
}

const workerId = getWorkerId();
const datacenterId = getDatacenterId();

/**
 * 生成下一个 uid，返回十进制字符串（64 位整数）。
 * @returns {string}
 */
function generateUid() {
  let now = Date.now();
  if (now < lastTimestamp) {
    now = lastTimestamp;
  }
  if (now === lastTimestamp) {
    sequence = (sequence + 1) & MAX_SEQUENCE;
    if (sequence === 0) {
      while (now <= lastTimestamp) {
        now = Date.now();
      }
      lastTimestamp = now;
    }
  } else {
    sequence = 0;
    lastTimestamp = now;
  }
  const ts = BigInt(now - EPOCH);
  const part = (ts << BigInt(TIMESTAMP_SHIFT)) |
    (BigInt(datacenterId) << BigInt(DATACENTER_SHIFT)) |
    (BigInt(workerId) << BigInt(WORKER_SHIFT)) |
    BigInt(sequence);
  return part.toString(10);
}

module.exports = { generateUid };
