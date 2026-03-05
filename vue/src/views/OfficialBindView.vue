<template>
  <div class="bind-page">
    <div class="bind-card">
      <div class="bind-card-accent"></div>
      <h1 class="bind-logo">
        <span class="bind-logo-line1">{{ t('official.landing.title') }}</span>
        <span class="bind-logo-line2 accent">{{ t('official.landing.titleSuffix') }}</span>
      </h1>
      <h2 class="bind-title">{{ t('official.bind.title') }}</h2>
      <p class="bind-desc">{{ t('official.bind.desc') }}</p>
      <template v-if="!code">
        <p class="bind-error">{{ t('official.bind.noCode') }}</p>
      </template>
      <template v-else-if="success">
        <p class="bind-success">{{ t('official.bind.success') }}</p>
      </template>
      <template v-else>
        <p class="bind-code-hint">{{ t('official.bind.codeHint') }}</p>
        <p class="bind-code">{{ code }}</p>
        <button
          type="button"
          class="bind-btn"
          :disabled="loading"
          @click="confirm"
        >
          {{ loading ? t('common.loading') : t('official.bind.confirmBtn') }}
        </button>
        <p v-if="error" class="bind-error">{{ error }}</p>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getToken } from '../api'
import { api } from '../api'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const code = computed(() => route.query.code || '')
const loading = ref(false)
const error = ref('')
const success = ref(false)

onMounted(() => {
  if (!code.value) return
  if (!getToken()) {
    const redirect = encodeURIComponent(route.fullPath)
    router.replace(`/login?redirect=${redirect}`)
  }
})

async function confirm() {
  if (!code.value) return
  loading.value = true
  error.value = ''
  try {
    await api.cli.bind.confirm(code.value)
    success.value = true
  } catch (e) {
    error.value = e.message || t('official.bind.confirmFailed')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.bind-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  font-family: 'Segoe UI', system-ui, sans-serif;
}
.bind-card {
  position: relative;
  width: 100%;
  max-width: 420px;
  background: var(--jt-card-bg);
  border-radius: 20px;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.1), 0 0 0 1px rgba(0, 0, 0, 0.04);
  padding: 2rem 1.75rem;
  border: 1px solid var(--jt-border);
}
[data-theme="dark"] .bind-card {
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.06);
}
.bind-card-accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--jt-primary), color-mix(in srgb, var(--jt-primary) 70%, transparent));
  border-radius: 20px 20px 0 0;
}
.bind-logo {
  margin: 0 0 0.5rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--jt-primary);
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1.25;
  letter-spacing: -0.02em;
}
.bind-logo-line1 { display: block; }
.bind-logo-line2 { display: block; font-size: 0.75em; margin-top: 0.1em; }
.bind-logo-line2.accent { color: var(--jt-primary); }
.bind-title {
  margin: 0 0 0.35rem;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--jt-text);
  text-align: center;
  letter-spacing: -0.01em;
}
.bind-desc {
  margin: 0 0 1.5rem;
  font-size: 0.9375rem;
  color: var(--jt-text-muted);
  text-align: center;
  line-height: 1.5;
}
.bind-code-hint {
  margin: 0 0 0.5rem;
  font-size: 0.875rem;
  color: var(--jt-text-muted);
  text-align: center;
}
.bind-code {
  margin: 0 0 1rem;
  font-family: ui-monospace, monospace;
  font-size: 1.125rem;
  font-weight: 600;
  text-align: center;
  letter-spacing: 0.1em;
  color: var(--jt-primary);
}
.bind-btn {
  width: 100%;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  font-weight: 600;
  color: white;
  background: var(--jt-primary);
  border: none;
  border-radius: 12px;
  cursor: pointer;
}
.bind-btn:hover:not(:disabled) {
  opacity: 0.9;
}
.bind-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.bind-success {
  margin: 0;
  font-size: 0.9375rem;
  color: var(--jt-primary);
  text-align: center;
  font-weight: 500;
}
.bind-error {
  margin: 1rem 0 0;
  font-size: 0.875rem;
  color: var(--jt-error, #c00);
  text-align: center;
}
</style>
