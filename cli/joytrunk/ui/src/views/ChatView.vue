<template>
  <div class="page">
    <h1 class="page-title">{{ t('chat.title') }}</h1>
    <div class="card">
      <label class="field">
        <span class="field-label">{{ t('chat.selectEmployee') }}</span>
        <select v-model="chatEmployeeId" class="field-input">
          <option value="">{{ t('chat.selectPlaceholder') }}</option>
          <option v-for="e in team?.employees || []" :key="e.id" :value="e.id">{{ e.name }}</option>
        </select>
      </label>
      <template v-if="chatEmployeeId">
        <label class="field">
          <span class="field-label">{{ t('chat.inputMessage') }}</span>
          <div class="input-row">
            <input v-model="chatInput" type="text" class="field-input" :placeholder="t('chat.inputPlaceholder')" @keydown.enter="sendChat" />
            <button type="button" class="btn primary" :disabled="chatSending || !chatInput.trim()" @click="sendChat">{{ t('chat.send') }}</button>
          </div>
        </label>
        <div v-if="chatReply" class="reply">{{ chatReply }}</div>
        <p v-if="chatUsage" class="muted">{{ chatUsage }}</p>
        <p v-if="chatError" class="error">{{ chatError }}</p>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '../api'

const { t } = useI18n()
const team = inject('team')
const chatEmployeeId = ref('')
const chatInput = ref('')
const chatReply = ref('')
const chatUsage = ref('')
const chatError = ref('')
const chatSending = ref(false)

async function sendChat() {
  if (!chatEmployeeId.value || !chatInput.value.trim()) return
  chatSending.value = true
  chatError.value = ''
  chatReply.value = ''
  try {
    const data = await api.employees.chat(chatEmployeeId.value, { content: chatInput.value })
    chatReply.value = data.reply
    chatUsage.value = data.usage ? t('chat.usageTemplate', { input: data.usage.input_tokens || 0, output: data.usage.output_tokens || 0 }) : ''
    chatInput.value = ''
  } catch (e) {
    chatError.value = e.message || t('chat.sendFailed')
  } finally {
    chatSending.value = false
  }
}
</script>

<style scoped>
.page { max-width: 560px; }
.page-title { margin: 0 0 1.25rem; font-size: 1.5rem; font-weight: 600; }
.card { background: var(--jt-card-bg); border-radius: var(--jt-radius); box-shadow: var(--jt-card-shadow); padding: 1.25rem 1.5rem; }
.field { display: block; margin-bottom: 1rem; }
.field-label { display: block; font-size: 0.875rem; font-weight: 500; margin-bottom: 0.35rem; color: var(--jt-text); }
.field-input { width: 100%; padding: 0.5rem 0.75rem; border: 1px solid var(--jt-border); border-radius: 6px; font-size: 0.9375rem; }
.input-row { display: flex; gap: 0.5rem; }
.input-row .field-input { flex: 1; }
.btn { padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.9375rem; cursor: pointer; border: none; }
.btn.primary { background: var(--jt-primary); color: #fff; }
.btn.primary:hover:not(:disabled) { background: var(--jt-primary-hover); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.reply { background: var(--jt-bg); border-radius: 6px; padding: 0.75rem 1rem; margin-top: 0.75rem; white-space: pre-wrap; font-size: 0.9375rem; border: 1px solid var(--jt-border); }
.muted { font-size: 0.875rem; color: var(--jt-text-muted); margin-top: 0.5rem; }
.error { color: #b91c1c; font-size: 0.875rem; margin-top: 0.5rem; }
</style>
