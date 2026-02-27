<template>
  <div class="dashboard">
    <header class="header">
      <h1>JoyTrunk 团队</h1>
      <p class="owner">负责人：{{ team?.owner?.name || '-' }}</p>
      <button v-if="token" type="button" class="btn outline" @click="logout">退出</button>
      <button v-else type="button" class="btn outline" @click="$emit('open-login')">绑定账号（可选）</button>
    </header>

    <section class="section">
      <h2>当前团队</h2>
      <p v-if="!team">加载中…</p>
      <div v-else>
        <p><strong>负责人</strong> {{ team.owner.name }}（{{ team.owner.id }}）</p>
        <h3>员工列表（{{ team.employees.length }}）</h3>
        <ul v-if="team.employees.length" class="emp-list">
          <li v-for="e in team.employees" :key="e.id">
            {{ e.name }}
            <span v-if="e.persona" class="muted"> · {{ e.persona }}</span>
            <span v-if="e.role" class="muted"> · {{ e.role }}</span>
          </li>
        </ul>
        <p v-else class="muted">暂无员工，下方创建。</p>
      </div>
    </section>

    <section class="section card">
      <h2>与员工对话</h2>
      <label>选择员工
        <select v-model="chatEmployeeId">
          <option value="">-- 请选择 --</option>
          <option v-for="e in team?.employees || []" :key="e.id" :value="e.id">{{ e.name }}</option>
        </select>
      </label>
      <div v-if="chatEmployeeId">
        <label>输入消息 <input v-model="chatInput" type="text" placeholder="输入后发送" @keydown.enter="sendChat" /></label>
        <button type="button" class="btn primary" :disabled="chatSending" @click="sendChat">发送</button>
        <p v-if="chatReply" class="reply">{{ chatReply }}</p>
        <p v-if="chatUsage" class="muted">本次用量：{{ chatUsage }}</p>
        <p v-if="chatError" class="error">{{ chatError }}</p>
      </div>
    </section>

    <section class="section card">
      <h2>创建员工</h2>
      <form @submit.prevent="createEmp">
        <label>名称 <input v-model="newName" type="text" placeholder="员工名称" required /></label>
        <label>人格（选填） <input v-model="newPersona" type="text" placeholder="如：温和、专业" /></label>
        <label>职责（选填） <input v-model="newRole" type="text" placeholder="如：助理、分析" /></label>
        <label>专长（选填） <input v-model="newSpecialty" type="text" placeholder="如：写作、数据" /></label>
        <button type="submit" class="btn primary" :disabled="creating">创建</button>
      </form>
      <p v-if="createError" class="error">{{ createError }}</p>
    </section>

    <section class="section card">
      <h2>设置</h2>
      <h3>用量</h3>
      <p v-if="usage">Router：{{ usage.usage?.find(u => u.source === 'router')?.tokens ?? 0 }} tokens · 自有 LLM：{{ usage.usage?.find(u => u.source === 'custom')?.tokens ?? 0 }} tokens（不计费）</p>
      <p v-else class="muted">加载中…</p>
      <h3>自有大模型（可选）</h3>
      <p class="muted">配置后员工将使用你的 API 回复，不经过 JoyTrunk Router，不计费。</p>
      <form @submit.prevent="saveCustomLLM">
        <label>API Key <input v-model="customLLM.apiKey" type="password" placeholder="sk-..." autocomplete="off" /></label>
        <label>Base URL <input v-model="customLLM.baseUrl" type="text" placeholder="https://api.openai.com/v1" /></label>
        <label>模型 <input v-model="customLLM.model" type="text" placeholder="gpt-3.5-turbo" /></label>
        <button type="submit" class="btn primary" :disabled="saving">保存</button>
        <button v-if="hasCustomLLM" type="button" class="btn outline" :disabled="saving" @click="clearCustomLLM">恢复默认（使用 JoyTrunk）</button>
      </form>
      <p v-if="configError" class="error">{{ configError }}</p>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api, getToken, clearToken } from '../api'

const team = ref(null)
const token = ref(null)
const newName = ref('')
const newPersona = ref('')
const newRole = ref('')
const newSpecialty = ref('')
const creating = ref(false)
const createError = ref('')
const chatEmployeeId = ref('')
const chatInput = ref('')
const chatReply = ref('')
const chatUsage = ref('')
const chatError = ref('')
const chatSending = ref(false)
const usage = ref(null)
const config = ref(null)
const customLLM = ref({ apiKey: '', baseUrl: '', model: '' })
const hasCustomLLM = ref(false)
const saving = ref(false)
const configError = ref('')

async function load() {
  try {
    team.value = await api.teams.current()
  } catch {
    team.value = null
  }
}

async function createEmp() {
  creating.value = true
  createError.value = ''
  try {
    await api.employees.create({
      name: newName.value,
      persona: newPersona.value || undefined,
      role: newRole.value || undefined,
      specialty: newSpecialty.value || undefined,
    })
    newName.value = ''
    newPersona.value = ''
    newRole.value = ''
    newSpecialty.value = ''
    await load()
  } catch (e) {
    createError.value = e.message || '创建失败'
  } finally {
    creating.value = false
  }
}

async function sendChat() {
  if (!chatEmployeeId.value || !chatInput.value.trim()) return
  chatSending.value = true
  chatError.value = ''
  chatReply.value = ''
  try {
    const data = await api.employees.chat(chatEmployeeId.value, { content: chatInput.value })
    chatReply.value = data.reply
    chatUsage.value = data.usage ? `输入 ${data.usage.input_tokens || 0} / 输出 ${data.usage.output_tokens || 0} tokens` : ''
    chatInput.value = ''
  } catch (e) {
    chatError.value = e.message || '发送失败'
  } finally {
    chatSending.value = false
  }
}

function logout() {
  clearToken()
  window.location.reload()
}

async function loadConfigAndUsage() {
  configError.value = ''
  try {
    const c = await api.config()
    config.value = c
    hasCustomLLM.value = !!(c.customLLM && (c.customLLM.apiKey || c.customLLM.baseUrl || c.customLLM.model))
    customLLM.value = {
      apiKey: c.customLLM?.apiKey === '***' ? '' : (c.customLLM?.apiKey || ''),
      baseUrl: c.customLLM?.baseUrl || '',
      model: c.customLLM?.model || '',
    }
  } catch (_) {}
  try {
    usage.value = await api.usage()
  } catch (_) {}
}

async function saveCustomLLM() {
  saving.value = true
  configError.value = ''
  try {
    await api.configPatchCustomLLM({
      apiKey: customLLM.value.apiKey || undefined,
      baseUrl: customLLM.value.baseUrl || undefined,
      model: customLLM.value.model || undefined,
    })
    await loadConfigAndUsage()
  } catch (e) {
    configError.value = e.message || '保存失败'
  } finally {
    saving.value = false
  }
}

async function clearCustomLLM() {
  saving.value = true
  configError.value = ''
  try {
    await api.configClearCustomLLM()
    customLLM.value = { apiKey: '', baseUrl: '', model: '' }
    hasCustomLLM.value = false
    await loadConfigAndUsage()
  } catch (e) {
    configError.value = e.message || '恢复失败'
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  token.value = getToken()
  load()
  loadConfigAndUsage()
})
</script>

<style scoped>
.dashboard { padding: 1rem 2rem; font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; }
.header { display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; }
.header h1 { margin: 0; flex: 1; }
.owner { margin: 0; color: #666; }
.section { margin-bottom: 1.5rem; }
.section h2 { margin-top: 0; }
.card { background: #f8f9fa; border-radius: 8px; padding: 1.5rem; }
.emp-list { list-style: none; padding-left: 0; }
.emp-list li { padding: 0.25rem 0; }
.muted { color: #666; font-size: 0.9rem; }
label { display: block; margin-bottom: 0.75rem; }
label input { width: 100%; max-width: 320px; padding: 0.5rem; margin-top: 0.25rem; box-sizing: border-box; }
.btn { padding: 0.5rem 1rem; cursor: pointer; border-radius: 4px; border: 1px solid #ccc; }
.btn.primary { background: #0d6efd; color: #fff; border-color: #0d6efd; }
.btn.outline { background: transparent; }
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.error { color: #dc3545; margin-top: 0.5rem; }
.reply { background: #e7f3ff; padding: 0.75rem; border-radius: 4px; margin-top: 0.5rem; white-space: pre-wrap; }
</style>
