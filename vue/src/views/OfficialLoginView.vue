<template>
  <div class="login-page">
    <div class="login-box">
      <h1 class="logo">JoyTrunk</h1>
      <h2 class="card-title">{{ t('official.login.title') }}</h2>
      <div class="tabs">
        <button
          type="button"
          class="tab"
          :class="{ active: tab === 'phone' }"
          @click="tab = 'phone'; error = ''"
        >
          {{ t('official.login.tabPhone') }}
        </button>
        <button
          type="button"
          class="tab"
          :class="{ active: tab === 'email' }"
          @click="tab = 'email'; error = ''"
        >
          {{ t('official.login.tabEmail') }}
        </button>
        <button
          type="button"
          class="tab"
          :class="{ active: tab === 'password' }"
          @click="tab = 'password'; error = ''"
        >
          {{ t('official.login.tabPassword') }}
        </button>
      </div>
      <!-- 手机验证码 -->
      <form v-if="tab === 'phone'" @submit.prevent="doLoginPhone" class="card">
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
              @click="sendPhoneCode"
            >
              {{ countdown > 0 ? t('official.login.sendCodeWait', { n: countdown }) : t('official.login.sendCode') }}
            </button>
          </div>
        </label>
        <button type="submit" class="btn primary" :disabled="loading">
          {{ t('official.login.login') }}
        </button>
      </form>
      <!-- 邮箱验证码 -->
      <form v-else-if="tab === 'email'" @submit.prevent="doLoginEmail" class="card">
        <label class="field">
          <span class="field-label">{{ t('official.login.email') }}</span>
          <input
            v-model="email"
            type="email"
            class="field-input"
            :placeholder="t('official.login.emailPlaceholder')"
            required
          />
        </label>
        <label class="field">
          <span class="field-label">{{ t('official.login.code') }}</span>
          <div class="code-row">
            <input
              v-model="emailCode"
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
              @click="sendEmailCode"
            >
              {{ countdown > 0 ? t('official.login.sendCodeWait', { n: countdown }) : t('official.login.sendCode') }}
            </button>
          </div>
        </label>
        <button type="submit" class="btn primary" :disabled="loading">
          {{ t('official.login.login') }}
        </button>
      </form>
      <!-- 密码登录 -->
      <form v-else @submit.prevent="doLoginPassword" class="card">
        <label class="field">
          <span class="field-label">{{ t('official.login.account') }}</span>
          <input
            v-model="account"
            type="text"
            class="field-input"
            :placeholder="t('official.login.accountPlaceholder')"
            required
          />
        </label>
        <label class="field">
          <span class="field-label">{{ t('official.login.password') }}</span>
          <input
            v-model="password"
            type="password"
            class="field-input"
            :placeholder="t('official.login.passwordPlaceholder')"
            required
          />
        </label>
        <button type="submit" class="btn primary" :disabled="loading">
          {{ t('official.login.login') }}
        </button>
      </form>
      <p class="toggle">
        <router-link to="/">{{ t('common.back') }}</router-link>
        <span class="sep"> · </span>
        <span>{{ t('official.login.noAccount') }}</span>
        <router-link to="/login?register=1">{{ t('official.login.register') }}</router-link>
      </p>
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
const tab = ref('phone')
const phone = ref('')
const code = ref('')
const email = ref('')
const emailCode = ref('')
const account = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const codeSent = ref(false)
const countdown = ref(0)
let countdownTimer = null

function startCountdown() {
  codeSent.value = true
  countdown.value = 60
  if (countdownTimer) clearInterval(countdownTimer)
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) clearInterval(countdownTimer)
  }, 1000)
}

async function sendPhoneCode() {
  if (!/^1\d{10}$/.test(phone.value)) {
    error.value = t('official.login.invalidPhone')
    return
  }
  error.value = ''
  codeSent.value = false
  try {
    await api.auth.sendCode({ phone: phone.value })
    startCountdown()
  } catch (e) {
    error.value = e.message || t('official.login.loginFailed')
  }
}

async function sendEmailCode() {
  const e = (email.value || '').trim().toLowerCase()
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e)) {
    error.value = t('official.login.invalidEmail')
    return
  }
  error.value = ''
  codeSent.value = false
  try {
    await api.auth.sendEmailCode({ email: e })
    startCountdown()
  } catch (e) {
    error.value = e.message || t('official.login.loginFailed')
  }
}

function onLoginSuccess(token) {
  setToken(token)
  router.push('/app')
}

async function doLoginPhone() {
  loading.value = true
  error.value = ''
  try {
    const { token } = await api.auth.loginByCode({ phone: phone.value, code: code.value })
    onLoginSuccess(token)
  } catch (e) {
    error.value = e.message || t('official.login.loginFailed')
  } finally {
    loading.value = false
  }
}

async function doLoginEmail() {
  loading.value = true
  error.value = ''
  try {
    const { token } = await api.auth.loginByEmailCode({
      email: (email.value || '').trim().toLowerCase(),
      code: emailCode.value,
    })
    onLoginSuccess(token)
  } catch (e) {
    error.value = e.message || t('official.login.loginFailed')
  } finally {
    loading.value = false
  }
}

async function doLoginPassword() {
  loading.value = true
  error.value = ''
  try {
    const { token } = await api.auth.loginByPassword({
      account: (account.value || '').trim(),
      password: password.value,
    })
    onLoginSuccess(token)
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
.tabs {
  display: flex;
  gap: 0.25rem;
  margin-bottom: 1rem;
}
.tab {
  flex: 1;
  padding: 0.4rem 0.5rem;
  font-size: 0.875rem;
  border: 1px solid var(--jt-border);
  border-radius: 6px;
  background: var(--jt-bg);
  color: var(--jt-text);
  cursor: pointer;
}
.tab:hover { background: var(--jt-card-bg); }
.tab.active {
  background: var(--jt-primary);
  color: #fff;
  border-color: var(--jt-primary);
}
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
