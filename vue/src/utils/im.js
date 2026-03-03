/**
 * IM 相关工具函数：截断、URL 校验、禁言判断等，供 ImGroupInfo、ImChatPane、ImConversationList 复用。
 */

/**
 * 截断文本，仅当超过 maxLen 时追加 '...'
 * @param {string|null|undefined} text
 * @param {number} maxLen
 * @returns {string}
 */
export function truncateText(text, maxLen = 20) {
  if (!text) return '';
  const t = String(text).trim();
  return t.length > maxLen ? t.slice(0, maxLen) + '...' : t;
}

/**
 * 校验是否为 http(s) URL（用于头像等）
 * @param {string|null|undefined} url
 * @returns {boolean}
 */
export function validateImageUrl(url) {
  return !!(url && String(url).trim().match(/^https?:\/\//i));
}

/**
 * 根据 muted_until 判断当前是否处于禁言中
 * @param {string|null|undefined} mutedUntil - ISO 字符串或 null
 * @returns {boolean}
 */
export function isMuted(mutedUntil) {
  return !!mutedUntil && new Date(mutedUntil).getTime() > Date.now();
}
