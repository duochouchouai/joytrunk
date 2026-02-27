/**
 * 中文文案（本地管理界面）
 */
export default {
  common: { loading: '加载中…', back: '返回', refresh: '刷新' },
  nav: { overview: '概览', chat: '对话', employees: '员工', settings: '设置', bindAccount: '绑定账号', logout: '退出', owner: '负责人' },
  home: { title: '概览', currentTeam: '当前团队', owner: '负责人', employeeCount: '员工 {n} 人', noEmployees: '暂无员工，请到「员工」页创建。' },
  chat: { title: '与员工对话', selectEmployee: '选择员工', selectPlaceholder: '请选择员工', inputMessage: '输入消息', inputPlaceholder: '输入后回车发送', send: '发送', usageTemplate: '本次用量：输入 {input} / 输出 {output} tokens', sendFailed: '发送失败' },
  employees: { title: '员工', create: '创建员工', list: '员工列表', name: '名称', namePlaceholder: '员工名称', persona: '人格（选填）', personaPlaceholder: '如：温和、专业', role: '职责（选填）', rolePlaceholder: '如：助理、分析', specialty: '专长（选填）', specialtyPlaceholder: '如：写作、数据', createBtn: '创建', noEmployees: '暂无员工。', createFailed: '创建失败', viewLogs: '日志' },
  logs: { title: '运行日志', backToEmployees: '返回员工列表', empty: '暂无日志。请通过 CLI（joytrunk chat）或本页对话与员工交互后查看。', loadFailed: '加载失败', runId: '会话', event: '事件', time: '时间', payload: '详情', eventLoopStart: '循环开始', eventIteration: '迭代', eventLlmRequest: '请求大模型', eventLlmResponse: '大模型回复', eventToolCalls: '工具调用', eventToolResult: '工具结果', eventFinalReply: '最终回复', eventMaxIterations: '达到最大迭代', eventLoopDone: '循环结束', eventAppendTurnDone: '历史已保存', sortOrder: '排序', sortNewestFirst: '最新在前', sortOldestFirst: '最早在前', filterByEvent: '按事件类型', filterByRunId: 'Run ID', filterByKeyword: '关键词搜索', filterPlaceholderRunId: '输入 run_id 筛选', filterPlaceholderKeyword: '搜索 payload 内容', filterAllEvents: '全部事件', resultCount: '共 {n} 条' },
  settings: { title: '设置', language: '语言', theme: '主题', themeLight: '浅色', themeDark: '深色', usage: '用量', usageRouter: 'Router：{n} tokens', usageCustom: '自有 LLM：{n} tokens（不计费）', customLLM: '自有大模型（可选）', customLLMHint: '配置后员工将使用你的 API 回复，不经过 JoyTrunk Router，不计费。', apiKey: 'API Key', baseUrl: 'Base URL', model: '模型', save: '保存', restoreDefault: '恢复默认', saveFailed: '保存失败', restoreFailed: '恢复失败' },
  login: { subtitle: '绑定账号（可选）— 用于使用 JoyTrunk 即时通讯', login: '登录', hint: '本地单用户：点击登录使用当前负责人。', register: '注册负责人', name: '名称', namePlaceholder: '负责人名称', email: '邮箱（选填）', emailPlaceholder: 'email', switchToRegister: '尚未注册？去注册', switchToLogin: '已有账号？去登录', loginFailed: '登录失败', registerFailed: '注册失败' },
}
