<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-card-accent"></div>
      <h1 class="login-logo">
        <span class="login-logo-line1">{{ t('official.landing.title') }}</span>
        <span class="login-logo-line2 accent">{{ t('official.landing.titleSuffix') }}</span>
      </h1>
      <h2 class="login-title">
        {{ mode === 'register' ? t('official.login.register') : t('official.login.title') }}
      </h2>
      <p class="login-desc">
        {{ mode === 'register' ? t('official.login.registerHint') : t('official.login.loginHint') }}
      </p>
      <AuthForm
        :mode="mode"
        :embedded="false"
        @success="onSuccess"
        @switch-register="goRegister"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { setToken } from '../api'
import AuthForm from '../components/AuthForm.vue'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()

const mode = computed(() => (route.query.register === '1' ? 'register' : 'login'))

function onSuccess(token) {
  setToken(token)
  const redirect = route.query.redirect
  router.push(typeof redirect === 'string' && redirect.startsWith('/') ? redirect : '/app/im')
}

function goRegister() {
  router.replace('/login?register=1')
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
.login-card {
  position: relative;
  width: 100%;
  max-width: 420px;
  background: var(--jt-card-bg);
  border-radius: 20px;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.1), 0 0 0 1px rgba(0, 0, 0, 0.04);
  padding: 2rem 1.75rem;
  border: 1px solid var(--jt-border);
}
[data-theme="dark"] .login-card {
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.06);
}
.login-card-accent {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--jt-primary), color-mix(in srgb, var(--jt-primary) 70%, transparent));
  border-radius: 20px 20px 0 0;
}
.login-logo {
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
.login-logo-line1 { display: block; }
.login-logo-line2 { display: block; font-size: 0.75em; margin-top: 0.1em; }
.login-logo-line2.accent { color: var(--jt-primary); }
.login-title {
  margin: 0 0 0.35rem;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--jt-text);
  text-align: center;
  letter-spacing: -0.01em;
}
.login-desc {
  margin: 0 0 1.5rem;
  font-size: 0.9375rem;
  color: var(--jt-text-muted);
  text-align: center;
  line-height: 1.5;
}
</style>
