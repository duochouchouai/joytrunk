/**
 * 邮件服务：发送验证码邮件。配置不完整时不发，打日志并返回 false。
 * 超时 3s。
 */
const nodemailer = require('nodemailer');
const config = require('../config/default');

const MAIL_TIMEOUT_MS = 3000;
let transporter = null;

function isConfigComplete() {
  return !!(config.MAIL_HOST && config.MAIL_USER && config.MAIL_PASS);
}

function getTransporter() {
  if (transporter) return transporter;
  if (!isConfigComplete()) return null;
  transporter = nodemailer.createTransport({
    host: config.MAIL_HOST,
    port: config.MAIL_PORT || 465,
    secure: config.MAIL_PORT === 465 || config.MAIL_PORT == null,
    auth: {
      user: config.MAIL_USER,
      pass: config.MAIL_PASS,
    },
  });
  return transporter;
}

/**
 * 发送验证码邮件。返回 true 表示发送成功，false 表示未配置/失败（已打日志）。
 * @param {string} toEmail - 收件人邮箱
 * @param {string} code - 6 位验证码
 */
async function sendVerificationEmail(toEmail, code) {
  if (!isConfigComplete()) return false;

  const trans = getTransporter();
  if (!trans) return false;

  const expireMin = Math.floor((config.CODE_EXPIRE_SECONDS ?? 300) / 60);
  const mailOptions = {
    from: config.MAIL_FROM || config.MAIL_USER,
    to: toEmail,
    subject: '您的验证码',
    text: `您的验证码是：${code}，${expireMin} 分钟内有效。`,
    html: `您的验证码是：<strong>${code}</strong>，${expireMin} 分钟内有效。`,
  };

  const timeout = new Promise((_, reject) => {
    setTimeout(() => reject(new Error('MAIL_TIMEOUT')), MAIL_TIMEOUT_MS);
  });

  try {
    await Promise.race([trans.sendMail(mailOptions), timeout]);
    return true;
  } catch (e) {
    const msg = e?.message || e?.code || String(e);
    const emailMask = toEmail.replace(/(.{2})(.*)(@.*)/, '$1***$3');
    console.error('Mail send failed:', emailMask, msg);
    return false;
  }
}

module.exports = { sendVerificationEmail, isConfigComplete };
