/**
 * English locale (local management UI)
 */
export default {
  common: { loading: 'Loading…', back: 'Back' },
  nav: { overview: 'Overview', chat: 'Chat', employees: 'Employees', settings: 'Settings', bindAccount: 'Bind account', logout: 'Log out', owner: 'Owner' },
  home: { title: 'Overview', currentTeam: 'Current team', owner: 'Owner', employeeCount: '{n} employee(s)', noEmployees: 'No employees yet. Create one on the Employees page.' },
  chat: { title: 'Chat with employee', selectEmployee: 'Select employee', selectPlaceholder: 'Select employee', inputMessage: 'Message', inputPlaceholder: 'Type and press Enter to send', send: 'Send', usageTemplate: 'Usage: {input} in / {output} out tokens', sendFailed: 'Send failed' },
  employees: { title: 'Employees', create: 'Create employee', list: 'Employee list', name: 'Name', namePlaceholder: 'Employee name', persona: 'Persona (optional)', personaPlaceholder: 'e.g. friendly, professional', role: 'Role (optional)', rolePlaceholder: 'e.g. assistant, analyst', specialty: 'Specialty (optional)', specialtyPlaceholder: 'e.g. writing, data', createBtn: 'Create', noEmployees: 'No employees.', createFailed: 'Create failed' },
  settings: { title: 'Settings', language: 'Language', theme: 'Theme', themeLight: 'Light', themeDark: 'Dark', usage: 'Usage', usageRouter: 'Router: {n} tokens', usageCustom: 'Custom LLM: {n} tokens (no charge)', customLLM: 'Custom LLM (optional)', customLLMHint: 'When set, employees use your API; requests do not go through JoyTrunk Router.', apiKey: 'API Key', baseUrl: 'Base URL', model: 'Model', save: 'Save', restoreDefault: 'Restore default', saveFailed: 'Save failed', restoreFailed: 'Restore failed' },
  login: { subtitle: 'Bind account (optional) — for JoyTrunk IM', login: 'Log in', hint: 'Single local user: click to use current owner.', register: 'Register owner', name: 'Name', namePlaceholder: 'Owner name', email: 'Email (optional)', emailPlaceholder: 'email', switchToRegister: 'No account? Register', switchToLogin: 'Have an account? Log in', loginFailed: 'Log in failed', registerFailed: 'Register failed' },
}
