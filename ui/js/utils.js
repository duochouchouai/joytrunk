/**
 * 主窗口复用工具：escapeHtml、parseThinkReply（<think> 解析）
 * 挂载到 window.MainWindowUtils，供 chat、agents 等模块使用。
 */
(function () {
  function escapeHtml(s) {
    if (s == null) return '';
    var div = document.createElement('div');
    div.textContent = String(s);
    return div.innerHTML;
  }

  /** 从 agent 回复中解析 <think>...</think> 块，返回 { thinking: string, content: string }；无 think 时 thinking 为 '' */
  function parseThinkReply(text) {
    if (text == null) text = '';
    var s = String(text);
    var thinking = '';
    var content = s;
    var re = /<think>([\s\S]*?)<\/think>/gi;
    var match;
    var parts = [];
    while ((match = re.exec(s)) !== null) {
      parts.push(match[1].trim());
    }
    if (parts.length > 0) {
      thinking = parts.join('\n\n');
      content = s.replace(re, '').trim();
    }
    return { thinking: thinking, content: content };
  }

  /** 转义 HTML 并保留换行：\n → <br>，用于聊天气泡内容展示 */
  function formatMessageContent(s) {
    if (s == null) return '';
    return escapeHtml(String(s)).replace(/\n/g, '<br>');
  }

  window.MainWindowUtils = {
    escapeHtml: escapeHtml,
    parseThinkReply: parseThinkReply,
    formatMessageContent: formatMessageContent
  };
})();
