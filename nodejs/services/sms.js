/**
 * 阿里云短信服务：发送验证码短信。配置不完整时不打 API，打日志并返回 false。
 * 超时 3s；首次调用时校验必填项。
 */
const config = require('../config/default');

const SMS_TIMEOUT_MS = 3000;
let configValidated = false;

function isConfigComplete() {
  return !!(
    config.SMS_PROVIDER === 'aliyun' &&
    config.SMS_ACCESS_KEY_ID &&
    config.SMS_ACCESS_KEY_SECRET &&
    config.SMS_SIGN_NAME &&
    config.SMS_TEMPLATE_CODE
  );
}

function validateConfigOnce() {
  if (configValidated) return;
  configValidated = true;
  if (config.SMS_PROVIDER === 'aliyun' && !isConfigComplete()) {
    console.warn('SMS config incomplete (SMS_ACCESS_KEY_ID, SMS_ACCESS_KEY_SECRET, SMS_SIGN_NAME, SMS_TEMPLATE_CODE), skip real send.');
  }
}

/**
 * 发送验证码短信。返回 true 表示发送成功，false 表示未配置/失败（已打日志）。
 * @param {string} phone - 手机号
 * @param {string} code - 6 位验证码
 */
async function sendVerificationSms(phone, code) {
  validateConfigOnce();
  if (!isConfigComplete()) return false;

  const Client = require('@alicloud/dysmsapi20170525').default;
  const { SendSmsRequest } = require('@alicloud/dysmsapi20170525');

  const conf = {
    accessKeyId: config.SMS_ACCESS_KEY_ID,
    accessKeySecret: config.SMS_ACCESS_KEY_SECRET,
    regionId: config.SMS_REGION_ID || 'cn-hangzhou',
    endpoint: 'https://' + (config.SMS_ENDPOINT || 'dysmsapi.aliyuncs.com'),
  };

  const request = new SendSmsRequest({
    phoneNumbers: phone,
    signName: config.SMS_SIGN_NAME,
    templateCode: config.SMS_TEMPLATE_CODE,
    templateParam: JSON.stringify({ code }),
  });

  const client = new Client(conf);

  const timeout = new Promise((_, reject) => {
    setTimeout(() => reject(new Error('SMS_TIMEOUT')), SMS_TIMEOUT_MS);
  });

  try {
    await Promise.race([client.sendSms(request), timeout]);
    return true;
  } catch (e) {
    const msg = e?.message || e?.code || String(e);
    const phoneMask = phone.length >= 7 ? phone.slice(0, 3) + '****' + phone.slice(-4) : '***';
    console.error('SMS send failed:', phoneMask, msg);
    return false;
  }
}

module.exports = { sendVerificationSms, isConfigComplete };
