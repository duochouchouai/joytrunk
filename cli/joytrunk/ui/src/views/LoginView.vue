<template>
  <div class="login-page">
    <div class="login-box">
      <h1 class="logo">JoyTrunk</h1>
      <p class="subtitle">{{ t('login.subtitle') }}</p>
      <div class="card">
        <template v-if="mode === 'login'">
          <h2 class="card-title">{{ t('login.login') }}</h2>
          <p class="hint">{{ t('login.hint') }}</p>
          <button type="button" class="btn primary" :disabled="loading" @click="doLogin">{{ t('login.login') }}</button>
        </template>
        <template v-else>
          <h2 class="card-title">{{ t('login.register') }}</h2>
          <form @submit.prevent="doRegister">
            <label class="field">
              <span class="field-label">{{ t('login.name') }}</span>
              <input v-model="name" type="text" class="field-input" :placeholder="t('login.namePlaceholder')" required />
            </label>
            <label class="field">
              <span class="field-label">{{ t('login.email') }}</span>
              <input v-model="email" type="email" class="field-input" :placeholder="t('login.emailPlaceholder')" />
            </label>
            <button type="submit" class="btn primary" :disabled="loading">{{ t('login.register') }}</button>
          </form>
        </template>
        <p class="toggle">
          <a href="#" @click.prevent="mode = mode === 'login' ? 'register' : 'login'">{{ mode === 'login' ? t('login.switchToRegister') : t('login.switchToLogin') }}</a>
          <span class="sep"> · </span>
          <router-link to="/">{{ t('common.back') }}</router-link>
        </p>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { api, setToken } from '../api'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const mode = ref(route.query.register ? 'register' : 'login')
const name = ref('')
const email = ref('')
const loading = ref(false)
const error = ref('')

async function doLogin() {
  loading.value = true
  error.value = ''
  try {
    const { token } = await api.auth.login()
    setToken(token)
    router.push('/')
  } catch (e) {
    error.value = e.message || t('login.loginFailed')
  } finally { loading.value = false }
}

async function doRegister() {
  loading.value = true
  error.value = ''
  try {
    const { token } = await api.auth.register({ name: name.value, email: email.value || undefined })
    setToken(token)
    router.push('/')
  } catch (e) {
    error.value = e.message || t('login.registerFailed')
  } finally { loading.value = false }
}
</script>

<style scoped>
.login-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 2rem; font-family: 'Segoe UI', system-ui, sans-serif; }
.login-box { max-width: 380px; width: 100%; }
.logo { margin: 0 0 0.25rem; font-size: 1.5rem; font-weight: 600; color: var(--jt-primary); }
.subtitle { color: var(--jt-text-muted); font-size: 0.875rem; margin-bottom: 1.5rem; }
.card { background: var(--jt-card-bg); border-radius: var(--jt-radius); box-shadow: var(--jt-card-shadow); padding: 1.5rem; border: 1px solid var(--jt-border); }
.card-title { margin: 0 0 0.5rem; font-size: 1.125rem; font-weight: 600; }
.hint { font-size: 0.875rem; color: var(--jt-text-muted); margin-bottom: 1rem; }
.field { display: block; margin-bottom: 0.75rem; }
.field-label { display: block; font-size: 0.875rem; font-weight: 500; margin-bottom: 0.35rem; }
.field-input { width: 100%; padding: 0.5rem 0.75rem; border: 1px solid var(--jt-border); border-radius: 6px; font-size: 0.9375rem; }
.btn { padding: 0.5rem 1rem; border-radius: 6px; font-size: 0.9375rem; cursor: pointer; border: none; }
.btn.primary { background: var(--jt-primary); color: #fff; }
.btn.primary:hover:not(:disabled) { background: var(--jt-primary-hover); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.toggle { margin-top: 1rem; font-size: 0.875rem; }
.toggle a, .toggle a:visited { color: var(--jt-primary); text-decoration: none; }
.toggle a:hover { text-decoration: underline; }
.sep { color: var(--jt-text-muted); }
.error { color: #b91c1c; font-size: 0.875rem; margin-top: 1rem; }
</style>
