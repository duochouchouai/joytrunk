/**
 * JoyTrunk 全局 config.json 默认结构：仅保留全局配置。
 * 每位员工作为独立 agent，使用各自 workspace/employees/<id>/config.json 覆盖全局配置。
 */

const DEFAULT_CONFIG = {
  version: 1,
  joytrunkRoot: null,
  ownerId: null,
  server: { host: 'localhost', port: 32890 },
  agents: { defaults: { defaultEmployeeId: null, model: 'gpt-3.5-turbo', maxTokens: 2048, temperature: 0.1 } },
  channels: { cli: { enabled: true }, web: { enabled: true }, feishu: { enabled: false }, telegram: { enabled: false }, qq: { enabled: false } },
  providers: { joytrunk: {}, custom: { apiKey: '', apiBase: null, model: 'gpt-3.5-turbo' } },
};

function migrateFromLegacy(data) {
  if (!data || typeof data !== 'object') return JSON.parse(JSON.stringify(DEFAULT_CONFIG));
  const server = data.server && typeof data.server === 'object' ? data.server : { host: 'localhost', port: data.gatewayPort ?? data.gateway?.port ?? 32890 };
  const agents = data.agents?.defaults ? data.agents : { defaults: { defaultEmployeeId: data.defaultEmployeeId ?? null, model: 'gpt-3.5-turbo', maxTokens: 2048, temperature: 0.1 } };
  const raw = data.customLLM || data.providers?.custom;
  const custom = raw && typeof raw === 'object' ? { apiKey: raw.apiKey ?? '', apiBase: raw.apiBase ?? raw.baseUrl ?? null, model: raw.model ?? 'gpt-3.5-turbo' } : DEFAULT_CONFIG.providers.custom;
  const providers = data.providers && typeof data.providers === 'object' ? { ...data.providers, custom } : { joytrunk: {}, custom };
  const channels = data.channels && typeof data.channels === 'object' ? data.channels : DEFAULT_CONFIG.channels;
  return {
    version: data.version ?? 1,
    joytrunkRoot: data.joytrunkRoot ?? null,
    ownerId: data.ownerId ?? null,
    server: { host: server.host ?? 'localhost', port: server.port ?? 32890 },
    agents: { defaults: agents.defaults },
    channels,
    providers,
  };
}

module.exports = { DEFAULT_CONFIG, migrateFromLegacy };
