<template>
  <div class="login-page">
    <div class="login-box">
      <h1 class="logo">JoyTrunk</h1>
      <h2 class="card-title">{{ t('official.login.title') }}</h2>
      <form @submit.prevent="doLogin" class="card">
        <label class="field">
          <span class="field-label">{{ t('official.login.phone') }}</span>
          <input
            v-model="phone"
            type="tel"
            class="field-input"
            :placeholder="t('official.login.phonePlaceholder')"
            maxlength="11"
            required
          />
        </label>
        <label class="field">
          <span class="field-label">{{ t('official.login.code') }}</span>
          <div class="code-row">
            <input
              v-model="code"
              type="text"
              class="field-input code-input"
              :placeholder="t('official.login.codePlaceholder')"
              maxlength="6"
              required
            />
            <button
              type="button"
              class="btn secondary"
              :disabled="countdown > 0 || loading"
              @click="sendCode"
            >
              {{ countdown > 0 ? t('official.login.sendCodeWait', { n: countdown }) : t('official.login.sendCode') }}
            </button>
          </div>
        </label>
        <button type="submit" class="btn primary" :disabled="loading">
          {{ t('official.login.login') }}
        </button>
        <p class="toggle">
          <router-link to="/">{{ t('common.back') }}</router-link>
          <span class="sep"> · </span>
          <span>{{ t('official.login.noAccount') }}</span>
          <router-link to="/login?register=1">{{ t('official.login.register') }}</router-link>
        </p>
      </form>
      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="codeSent" class="success">{{ t('official.login.codeSent') }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { api, setToken } from '../api'

const { t } = useI18n()
const router = useRouter()
const phone = ref('')
const code = ref('')
const loading = ref(false)
const error = ref('')
const codeSent = ref(false)
const countdown = ref(0)
let countdownTimer = null

async function sendCode() {
  if (!/^1\d{10}$/.test(phone.value)) {
    error.value = '请输入正确的手机号'
    return
  }
  error.value = ''
  codeSent.value = false
  try {
    await api.auth.sendCode({ phone: phone.value })
    codeSent.value = true
    countdown.value = 60
    countdownTimer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) clearInterval(countdownTimer)
    }, 1000)
  } catch (e) {
    error.value = e.message || '发送失败'
  }
}

async function doLogin() {
  loading.value = true
  error.value = ''
  try {
    const { token } = await api.auth.loginByCode({ phone: phone.value, code: code.value })
    setToken(token)
    router.push('/app')
  } catch (e) {
    error.value = e.message || t('official.login.loginFailed')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  font-family: 'Segoe UI', system-ui, sans-serif;
}
.login-box { max-width: 380px; width: 100%; }
.logo { margin: 0 0 0.25rem; font-size: 1.5rem; font-weight: 600; color: var(--jt-primary); }
.card-title { margin: 0 0 1rem; font-size: 1.125rem; font-weight: 600; }
.card {
  background: var(--jt-card-bg);
  border-radius: var(--jt-radius);
  box-shadow: var(--jt-card-shadow);
  padding: 1.5rem;
  border: 1px solid var(--jt-border);
}
.field { display: block; margin-bottom: 1rem; }
.field-label { display: block; font-size: 0.875rem; font-weight: 500; margin-bottom: 0.35rem; }
.field-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--jt-border);
  border-radius: 6px;
  font-size: 0.9375rem;
}
.code-row { display: flex; gap: 0.5rem; }
.code-input { flex: 1; }
.btn { padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.9375rem; cursor: pointer; border: none; }
.btn.primary { background: var(--jt-primary); color: #fff; width: 100%; margin-top: 0.25rem; }
.btn.primary:hover:not(:disabled) { background: var(--jt-primary-hover); }
.btn.primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn.secondary { background: var(--jt-bg); color: var(--jt-text); border: 1px solid var(--jt-border); white-space: nowrap; }
.btn.secondary:hover:not(:disabled) { background: var(--jt-card-bg); }
.btn.secondary:disabled { opacity: 0.5; cursor: not-allowed; }
.toggle { margin-top: 1rem; font-size: 0.875rem; }
.toggle a { color: var(--jt-primary); text-decoration: none; }
.toggle a:hover { text-decoration: underline; }
.sep { color: var(--jt-text-muted); margin: 0 0.25rem; }
.error { color: #b91c1c; font-size: 0.875rem; margin-top: 1rem; }
.success { color: var(--jt-primary); font-size: 0.875rem; margin-top: 0.5rem; }
</style>
