<template>
  <div class="page" :class="{ 'page-mobile': isMobile }">
    <template v-if="isMobile">
      <MobileTitleBar :title="t('token.title')" />
      <div class="mobile-content">
        <section class="section-card">
          <h2 class="section-title">{{ t('token.apiKey') }}</h2>
          <p class="section-desc">{{ t('token.apiKeyHint') }}</p>
          <div class="key-row">
            <input
              :value="displayKey"
              type="text"
              class="field-input key-input"
              readonly
              :placeholder="me?.api_key_masked ? '' : t('token.empty')"
            />
            <button
              type="button"
              class="btn-primary"
              :disabled="generating"
              @click="generateKey"
            >
              {{ generating ? t('common.loading') : t('token.generateKey') }}
            </button>
          </div>
          <p v-if="justGenerated" class="msg msg-success">{{ t('token.generated') }}</p>
          <p v-if="copySuccess" class="msg msg-success">{{ t('token.copied') }}</p>
          <p v-if="keyError" class="msg msg-error">{{ keyError }}</p>
        </section>
        <section class="section-card">
          <h2 class="section-title">{{ t('token.balance') }}</h2>
          <div class="prefs-card">
            <div class="pref-row">
              <span class="pref-label">{{ t('token.balance') }}</span>
              <span class="pref-value">{{ (usage?.balance ?? 0).toLocaleString() }}</span>
            </div>
            <div class="pref-row">
              <span class="pref-label">{{ t('token.quota') }}</span>
              <span class="pref-value">{{ (usage?.quota ?? 0).toLocaleString() }}</span>
            </div>
          </div>
        </section>
        <section class="section-card">
          <h2 class="section-title">{{ t('token.router') }}</h2>
          <div class="prefs-card">
            <div class="pref-row">
              <span class="pref-label">{{ t('token.router') }}</span>
              <span class="pref-value num">{{ (routerTokens ?? 0).toLocaleString() }}</span>
            </div>
            <div class="pref-row">
              <span class="pref-label">{{ t('token.custom') }}</span>
              <span class="pref-value num">{{ (customTokens ?? 0).toLocaleString() }}</span>
            </div>
          </div>
        </section>
      </div>
    </template>
    <template v-else>
      <h1 class="page-title">{{ t('token.title') }}</h1>
      <!-- API Key 区块 -->
      <section class="section-card">
        <h2 class="section-title">{{ t('token.apiKey') }}</h2>
        <p class="section-desc">{{ t('token.apiKeyHint') }}</p>
        <div class="key-row">
          <input
            :value="displayKey"
            type="text"
            class="field-input key-input"
            readonly
            :placeholder="me?.api_key_masked ? '' : t('token.empty')"
          />
          <button
            type="button"
            class="btn-primary"
            :disabled="generating"
            @click="generateKey"
          >
            {{ generating ? t('common.loading') : t('token.generateKey') }}
          </button>
        </div>
        <p v-if="justGenerated" class="msg msg-success">{{ t('token.generated') }}</p>
        <p v-if="copySuccess" class="msg msg-success">{{ t('token.copied') }}</p>
        <p v-if="keyError" class="msg msg-error">{{ keyError }}</p>
      </section>

      <!-- 余额与额度 -->
      <section class="section-card">
        <h2 class="section-title">{{ t('token.balance') }}</h2>
        <div class="prefs-card">
          <div class="pref-row">
            <span class="pref-label">{{ t('token.balance') }}</span>
            <span class="pref-value">{{ (usage?.balance ?? 0).toLocaleString() }}</span>
          </div>
          <div class="pref-row">
            <span class="pref-label">{{ t('token.quota') }}</span>
            <span class="pref-value">{{ (usage?.quota ?? 0).toLocaleString() }}</span>
          </div>
        </div>
      </section>

      <section class="section-card">
        <h2 class="section-title">{{ t('token.router') }}</h2>
        <div class="prefs-card">
          <div class="pref-row">
            <span class="pref-label">{{ t('token.router') }}</span>
            <span class="pref-value num">{{ (routerTokens ?? 0).toLocaleString() }}</span>
          </div>
          <div class="pref-row">
            <span class="pref-label">{{ t('token.custom') }}</span>
            <span class="pref-value num">{{ (customTokens ?? 0).toLocaleString() }}</span>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '../api'
import MobileTitleBar from '../components/MobileTitleBar.vue'

const { t } = useI18n()
const isMobile = inject('isMobile', null)
const me = ref(null)
const usage = ref(null)
const generating = ref(false)
const justGenerated = ref(false)
const copySuccess = ref(false)
const keyError = ref('')
const newKeyOnce = ref(null)

const displayKey = computed(() => newKeyOnce.value || me.value?.api_key_masked || '')

const routerTokens = computed(() =>
  usage.value?.usage?.find(u => u.source === 'router')?.tokens ?? 0
)
const customTokens = computed(() =>
  usage.value?.usage?.find(u => u.source === 'custom')?.tokens ?? 0
)

async function loadMe() {
  try {
    me.value = await api.users.me()
  } catch {
    me.value = null
  }
}

async function loadUsage() {
  try {
    usage.value = await api.users.usage()
  } catch {
    usage.value = null
  }
}

async function generateKey() {
  keyError.value = ''
  justGenerated.value = false
  generating.value = true
  try {
    const { api_key } = await api.users.generateApiKey()
    newKeyOnce.value = api_key
    justGenerated.value = true
    setTimeout(() => { justGenerated.value = false }, 4000)
    await loadMe()
    try {
      await navigator.clipboard.writeText(api_key)
      copySuccess.value = true
      setTimeout(() => { copySuccess.value = false }, 2000)
    } catch {
      /* ignore */
    }
  } catch (e) {
    keyError.value = e.message || '生成失败'
  } finally {
    generating.value = false
  }
}

watch(displayKey, (val) => {
  if (newKeyOnce.value && !val) newKeyOnce.value = null
})

onMounted(() => {
  loadMe()
  loadUsage()
})
</script>

<style scoped>
.page {
  max-width: 520px;
  margin: 0 auto;
  padding-bottom: 2rem;
}
.page-mobile {
  max-width: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  min-height: 100%;
  overflow: auto;
}
.page-mobile .mobile-content {
  flex: 1;
  padding: 1rem;
  padding-bottom: 2rem;
}
.page-title {
  margin: 0 0 1.75rem;
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--jt-text);
}

.section-card {
  padding: 1.75rem 1.5rem;
  margin-bottom: 1.5rem;
  background: var(--jt-card-bg);
  border: 1px solid var(--jt-border);
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.section-title {
  margin: 0 0 0.5rem;
  font-size: 1.0625rem;
  font-weight: 600;
  color: var(--jt-text);
}

.section-desc {
  margin: 0 0 1rem;
  font-size: 0.875rem;
  color: var(--jt-text-muted, #64748b);
}

.key-row {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}

.key-input {
  flex: 1;
  min-width: 200px;
  font-family: ui-monospace, monospace;
  font-size: 0.875rem;
}

.field-input {
  width: 100%;
  padding: 0.65rem 0.9rem;
  border: 1px solid var(--jt-border);
  border-radius: 10px;
  font-size: 0.9375rem;
  background: var(--jt-bg);
  color: var(--jt-text);
}

.field-input:focus {
  outline: none;
  border-color: var(--jt-primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--jt-primary) 18%, transparent);
}

.btn-primary {
  padding: 0.65rem 1.25rem;
  border-radius: 10px;
  font-size: 0.9375rem;
  font-weight: 500;
  background: var(--jt-primary);
  color: #fff;
  border: none;
  cursor: pointer;
  transition: opacity 0.15s, transform 0.1s;
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.92;
  transform: translateY(-1px);
}

.btn-primary:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.prefs-card {
  background: var(--jt-bg);
  border: 1px solid var(--jt-border);
  border-radius: 14px;
  overflow: visible;
}

.pref-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  gap: 1rem;
  border-bottom: 1px solid var(--jt-border);
}

.pref-row:last-child {
  border-bottom: none;
}

.pref-label {
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--jt-text);
}

.pref-value {
  font-size: 0.9375rem;
  color: var(--jt-text-muted, #64748b);
}

.pref-value.num {
  font-variant-numeric: tabular-nums;
  font-weight: 600;
  color: var(--jt-primary);
}

.msg {
  font-size: 0.875rem;
  margin: 0.75rem 0 0;
}

.msg-error {
  color: #dc2626;
}

.msg-success {
  color: var(--jt-primary);
  font-weight: 500;
}
</style>
