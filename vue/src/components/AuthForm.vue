<template>
  <div class="auth-form">
    <div class="auth-tabs">
      <button
        type="button"
        class="auth-tab"
        :class="{ active: tab === 'phone' }"
        @click="tab = 'phone'; error = ''"
      >
        {{ t('official.login.tabPhone') }}
      </button>
      <button
        type="button"
        class="auth-tab"
        :class="{ active: tab === 'email' }"
        @click="tab = 'email'; error = ''"
      >
        {{ t('official.login.tabEmail') }}
      </button>
      <button
        type="button"
        class="auth-tab"
        :class="{ active: tab === 'password' }"
        @click="tab = 'password'; error = ''"
      >
        {{ t('official.login.tabPassword') }}
      </button>
    </div>

    <form v-if="tab === 'phone'" @submit.prevent="doLoginPhone" class="auth-fields">
      <label class="auth-field">
        <span class="auth-label">{{ t('official.login.phone') }}</span>
        <input
          v-model="phone"
          type="tel"
          class="auth-input"
          :placeholder="t('official.login.phonePlaceholder')"
          maxlength="11"
          required
        />
      </label>
      <label class="auth-field">
        <span class="auth-label">{{ t('official.login.code') }}</span>
        <div class="auth-code-row">
          <input
            v-model="code"
            type="text"
            class="auth-input auth-code-input"
            :placeholder="t('official.login.codePlaceholder')"
            maxlength="6"
            required
          />
          <button
            type="button"
            class="auth-btn-code"
            :disabled="countdown > 0 || loading"
            @click="sendPhoneCode"
          >
            {{ countdown > 0 ? t('official.login.sendCodeWait', { n: countdown }) : t('official.login.sendCode') }}
          </button>
        </div>
      </label>
      <button type="submit" class="auth-submit" :disabled="loading">
        {{ submitLabel }}
      </button>
    </form>

    <form v-else-if="tab === 'email'" @submit.prevent="doLoginEmail" class="auth-fields">
      <label class="auth-field">
        <span class="auth-label">{{ t('official.login.email') }}</span>
        <input
          v-model="email"
          type="email"
          class="auth-input"
          :placeholder="t('official.login.emailPlaceholder')"
          required
        />
      </label>
      <label class="auth-field">
        <span class="auth-label">{{ t('official.login.code') }}</span>
        <div class="auth-code-row">
          <input
            v-model="emailCode"
            type="text"
            class="auth-input auth-code-input"
            :placeholder="t('official.login.codePlaceholder')"
            maxlength="6"
            required
          />
          <button
            type="button"
            class="auth-btn-code"
            :disabled="countdown > 0 || loading"
            @click="sendEmailCode"
          >
            {{ countdown > 0 ? t('official.login.sendCodeWait', { n: countdown }) : t('official.login.sendCode') }}
          </button>
        </div>
      </label>
      <button type="submit" class="auth-submit" :disabled="loading">
        {{ submitLabel }}
      </button>
    </form>

    <form v-else @submit.prevent="doLoginPassword" class="auth-fields">
      <label class="auth-field">
        <span class="auth-label">{{ t('official.login.account') }}</span>
        <input
          v-model="account"
          type="text"
          class="auth-input"
          :placeholder="t('official.login.accountPlaceholder')"
          required
        />
      </label>
      <label class="auth-field">
        <span class="auth-label">{{ t('official.login.password') }}</span>
        <input
          v-model="password"
          type="password"
          class="auth-input"
          :placeholder="t('official.login.passwordPlaceholder')"
          required
        />
      </label>
      <button type="submit" class="auth-submit" :disabled="loading">
        {{ submitLabel }}
      </button>
    </form>

    <p v-if="error" class="auth-error">{{ error }}</p>
    <p v-if="codeSent" class="auth-success">{{ t('official.login.codeSent') }}</p>

    <p v-if="!embedded" class="auth-footer">
      <router-link to="/">{{ t('common.back') }}</router-link>
      <span class="auth-sep"> · </span>
      <span>{{ t('official.login.noAccount') }}</span>
      <a href="#" @click.prevent="$emit('switchRegister')">{{ t('official.login.register') }}</a>
    </p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '../api'

const props = defineProps({
  mode: { type: String, default: 'login' },
  embedded: { type: Boolean, default: false },
})
const emit = defineEmits(['success', 'switchRegister'])

const { t } = useI18n()
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

const submitLabel = computed(() =>
  props.mode === 'register' ? t('official.login.register') : t('official.login.login')
)

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

function onSuccess(token) {
  emit('success', token)
}

async function doLoginPhone() {
  loading.value = true
  error.value = ''
  try {
    const { token } = await api.auth.loginByCode({ phone: phone.value, code: code.value })
    onSuccess(token)
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
    onSuccess(token)
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
    onSuccess(token)
  } catch (e) {
    error.value = e.message || t('official.login.loginFailed')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-form { width: 100%; }
.auth-tabs {
  display: flex;
  gap: 0.35rem;
  margin-bottom: 1.25rem;
}
.auth-tab {
  flex: 1;
  padding: 0.5rem 0.6rem;
  font-size: 0.8125rem;
  font-weight: 500;
  border: 1px solid var(--jt-border);
  border-radius: 10px;
  background: var(--jt-bg);
  color: var(--jt-text-muted);
  cursor: pointer;
  transition: all 0.2s ease;
}
.auth-tab:hover { color: var(--jt-text); background: var(--jt-card-bg); }
.auth-tab.active {
  background: var(--jt-primary);
  color: #fff;
  border-color: var(--jt-primary);
}
.auth-fields { display: flex; flex-direction: column; gap: 1rem; }
.auth-field { display: block; }
.auth-label {
  display: block;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--jt-text-muted);
  margin-bottom: 0.4rem;
}
.auth-input {
  width: 100%;
  padding: 0.65rem 0.9rem;
  border: 1px solid var(--jt-border);
  border-radius: 10px;
  font-size: 0.9375rem;
  background: var(--jt-bg);
  color: var(--jt-text);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.auth-input::placeholder { color: var(--jt-text-muted); opacity: 0.8; }
.auth-input:hover { border-color: var(--jt-text-muted); }
.auth-input:focus {
  outline: none;
  border-color: var(--jt-primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--jt-primary) 18%, transparent);
}
.auth-code-row { display: flex; gap: 0.5rem; }
.auth-code-input { flex: 1; }
.auth-btn-code {
  padding: 0.65rem 1rem;
  font-size: 0.8125rem;
  font-weight: 500;
  border: 1px solid var(--jt-border);
  border-radius: 10px;
  background: var(--jt-card-bg);
  color: var(--jt-primary);
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.2s ease, border-color 0.2s ease;
}
.auth-btn-code:hover:not(:disabled) {
  background: color-mix(in srgb, var(--jt-primary) 10%, transparent);
  border-color: var(--jt-primary);
}
.auth-btn-code:disabled { opacity: 0.5; cursor: not-allowed; }
.auth-submit {
  width: 100%;
  margin-top: 0.5rem;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
  background: var(--jt-primary);
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: opacity 0.2s ease, transform 0.05s ease;
}
.auth-submit:hover:not(:disabled) { opacity: 0.92; }
.auth-submit:active:not(:disabled) { transform: scale(0.99); }
.auth-submit:disabled { opacity: 0.6; cursor: not-allowed; }
.auth-error { color: #dc2626; font-size: 0.875rem; margin-top: 0.75rem; }
.auth-success { color: var(--jt-primary); font-size: 0.875rem; margin-top: 0.5rem; }
.auth-footer { margin-top: 1.25rem; font-size: 0.875rem; color: var(--jt-text-muted); }
.auth-footer a { color: var(--jt-primary); text-decoration: none; }
.auth-footer a:hover { text-decoration: underline; }
.auth-sep { margin: 0 0.25rem; }
</style>
