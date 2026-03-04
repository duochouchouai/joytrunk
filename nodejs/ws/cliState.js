/** user_id -> WebSocket（一用户一 CLI），供 cliWs 与 pendingCliTasks 共用 */
const userIdToCliWs = new Map();

function getCliWsByUserId(userId) {
  return userIdToCliWs.get(Number(userId)) || null;
}

module.exports = { userIdToCliWs, getCliWsByUserId };
