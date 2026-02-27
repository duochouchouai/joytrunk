<template>
  <div class="page">
    <h1 class="page-title">{{ t('settings.title') }}</h1>
    <div class="card">
      <h2 class="card-title">{{ t('settings.language') }}</h2>
      <select v-model="locale" class="field-input field-select" @change="onLocaleChange">
        <option value="zh">简体中文</option>
        <option value="en">English</option>
      </select>
    </div>
    <div class="card">
      <h2 class="card-title">{{ t('settings.theme') }}</h2>
      <select v-model="theme" class="field-input field-select" @change="onThemeChange">
        <option value="light">{{ t('settings.themeLight') }}</option>
        <option value="dark">{{ t('settings.themeDark') }}</option>
      </select>
    </div>
    <div class="card">
      <h2 class="card-title">{{ t('settings.usage') }}</h2>
      <p v-if="usage">{{ t('settings.usageRouter', { n: usage.usage?.find(u => u.source === 'router')?.tokens ?? 0 }) }} · {{ t('settings.usageCustom', { n: usage.usage?.find(u => u.source === 'custom')?.tokens ?? 0 }) }}</p>
      <p v-else class="muted">{{ t('common.loading') }}</p>
    </div>
    <div class="card">
      <h2 class="card-title">{{ t('settings.customLLM') }}</h2>
      <p class="hint">{{ t('settings.customLLMHint') }}</p>
      <form @submit.prevent="saveCustomLLM" class="form">
        <label class="field">
          <span class="field-label">{{ t('settings.apiKey') }}</span>
          <input v-model="customLLM.apiKey" type="password" class="field-input" placeholder="sk-..." autocomplete="off" />
        </label>
        <label class="field">
          <span class="field-label">{{ t('settings.baseUrl') }}</span>
          <input v-model="customLLM.baseUrl" type="text" class="field-input" placeholder="https://api.openai.com/v1" />
        </label>
        <label class="field">
          <span class="field-label">{{ t('settings.model') }}</span>
          <input v-model="customLLM.model" type="text" class="field-input" placeholder="gpt-3.5-turbo" />
        </label>
        <div class="actions">
          <button type="submit" class="btn primary" :disabled="saving">{{ t('settings.save') }}</button>
          <button v-if="hasCustomLLM" type="button" class="btn outline" :disabled="saving" @click="clearCustomLLM">{{ t('settings.restoreDefault') }}</button>
        </div>
      </form>
      <p v-if="configError" class="error">{{ configError }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTheme } from '../composables/useTheme'
import { setLocale } from '../i18n'
import { api } from '../api'

const { t, locale } = useI18n()
const { theme, setTheme } = useTheme()
const team = inject('team')
const usage = ref(null)
const customLLM = ref({ apiKey: '', baseUrl: '', model: '' })
const hasCustomLLM = ref(false)
const saving = ref(false)
const configError = ref('')

async function loadConfigAndUsage() {
  configError.value = ''
  try {
    const c = await api.config()
    hasCustomLLM.value = !!(c.customLLM && (c.customLLM.apiKey || c.customLLM.baseUrl || c.customLLM.model))
    customLLM.value = { apiKey: c.customLLM?.apiKey === '***' ? '' : (c.customLLM?.apiKey || ''), baseUrl: c.customLLM?.baseUrl || '', model: c.customLLM?.model || '' }
  } catch (_) {}
  try { usage.value = await api.usage() } catch (_) {}
}

async function saveCustomLLM() {
  saving.value = true
  configError.value = ''
  try {
    await api.configPatchCustomLLM({ apiKey: customLLM.value.apiKey || undefined, baseUrl: customLLM.value.baseUrl || undefined, model: customLLM.value.model || undefined })
    await loadConfigAndUsage()
  } catch (e) {
    configError.value = e.message || t('settings.saveFailed')
  } finally { saving.value = false }
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
    configError.value = e.message || t('settings.restoreFailed')
  } finally { saving.value = false }
}

function onLocaleChange() { setLocale(locale.value) }
function onThemeChange() { setTheme(theme.value) }
onMounted(loadConfigAndUsage)
</script>

<style scoped>
.page { max-width: 560px; }
.page-title { margin: 0 0 1.25rem; font-size: 1.5rem; font-weight: 600; }
.card { background: var(--jt-card-bg); border-radius: var(--jt-radius); box-shadow: var(--jt-card-shadow); padding: 1.25rem 1.5rem; margin-bottom: 1rem; }
.card-title { margin: 0 0 0.5rem; font-size: 1rem; font-weight: 600; }
.hint { font-size: 0.875rem; color: var(--jt-text-muted); margin-bottom: 1rem; }
.form { margin-top: 0.5rem; }
.field { display: block; margin-bottom: 0.75rem; }
.field-label { display: block; font-size: 0.875rem; font-weight: 500; margin-bottom: 0.35rem; }
.field-input { width: 100%; max-width: 360px; padding: 0.5rem 0.75rem; border: 1px solid var(--jt-border); border-radius: 6px; font-size: 0.9375rem; }
.actions { display: flex; gap: 0.5rem; margin-top: 0.75rem; }
.btn { padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.9375rem; cursor: pointer; }
.btn.primary { background: var(--jt-primary); color: #fff; border: none; }
.btn.primary:hover:not(:disabled) { background: var(--jt-primary-hover); }
.btn.outline { background: transparent; border: 1px solid var(--jt-border); color: var(--jt-text); }
.btn.outline:hover:not(:disabled) { background: var(--jt-bg); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.error { color: #b91c1c; font-size: 0.875rem; margin-top: 0.5rem; }
.muted { font-size: 0.875rem; color: var(--jt-text-muted); }
.field-select { max-width: 200px; }
</style>
