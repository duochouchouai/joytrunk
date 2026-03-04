<template>
  <Teleport to="body">
    <Transition name="auth-modal">
      <div
        v-if="show"
        class="auth-modal-backdrop"
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-modal-title"
        @click.self="close"
      >
        <div class="auth-modal-card">
          <div class="auth-modal-accent"></div>
          <button
            type="button"
            class="auth-modal-close"
            aria-label="关闭"
            @click="close"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </button>
          <div class="auth-modal-body">
            <h2 id="auth-modal-title" class="auth-modal-title">
              {{ currentMode === 'register' ? t('official.login.register') : t('official.login.title') }}
            </h2>
            <p class="auth-modal-desc">
              {{ currentMode === 'register' ? t('official.login.registerHint') : t('official.login.loginHint') }}
            </p>
            <AuthForm
              ref="formRef"
              :mode="currentMode"
              :embedded="true"
              @success="onSuccess"
            />
            <p class="auth-modal-switch">
              <template v-if="currentMode === 'register'">
                <span>{{ t('official.login.hasAccount') }}</span>
                <button type="button" class="auth-modal-link" @click="emit('update:mode', 'login')">
                  {{ t('official.login.login') }}
                </button>
              </template>
              <template v-else>
                <span>{{ t('official.login.noAccount') }}</span>
                <button type="button" class="auth-modal-link" @click="emit('update:mode', 'register')">
                  {{ t('official.login.register') }}
                </button>
              </template>
            </p>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { setToken } from '../api'
import AuthForm from './AuthForm.vue'

const props = defineProps({
  show: { type: Boolean, default: false },
  mode: { type: String, default: 'login' },
})
const emit = defineEmits(['close', 'success', 'update:mode'])

const { t } = useI18n()
const formRef = ref(null)
const currentMode = computed(() => props.mode)

watch(() => props.show, (visible) => {
  if (visible) document.body.style.overflow = 'hidden'
  else document.body.style.overflow = ''
})

function close() {
  emit('close')
}

function onSuccess(token) {
  setToken(token)
  emit('success', token)
  document.body.style.overflow = ''
}
</script>

<style scoped>
.auth-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}
.auth-modal-card {
  position: relative;
  width: 100%;
  max-width: 420px;
  background: var(--jt-card-bg);
  border-radius: 20px;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.18), 0 0 0 1px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}
[data-theme="dark"] .auth-modal-card {
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.06);
}
.auth-modal-accent {
  height: 4px;
  background: linear-gradient(90deg, var(--jt-primary), color-mix(in srgb, var(--jt-primary) 70%, transparent));
}
.auth-modal-close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: var(--jt-text-muted);
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease;
}
.auth-modal-close:hover {
  background: var(--jt-bg);
  color: var(--jt-text);
}
.auth-modal-body {
  padding: 2rem 1.75rem 1.75rem;
}
.auth-modal-title {
  margin: 0 0 0.35rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--jt-text);
  letter-spacing: -0.02em;
  line-height: 1.25;
}
.auth-modal-desc {
  margin: 0 0 1.5rem;
  font-size: 0.9375rem;
  color: var(--jt-text-muted);
  line-height: 1.5;
}
.auth-modal-switch {
  margin-top: 1.25rem;
  padding-top: 1rem;
  border-top: 1px solid var(--jt-border);
  font-size: 0.875rem;
  color: var(--jt-text-muted);
}
.auth-modal-link {
  margin-left: 0.35rem;
  padding: 0;
  font: inherit;
  color: var(--jt-primary);
  background: none;
  border: none;
  cursor: pointer;
  text-decoration: none;
}
.auth-modal-link:hover { text-decoration: underline; }

.auth-modal-enter-active,
.auth-modal-leave-active { transition: opacity 0.2s ease; }
.auth-modal-enter-active .auth-modal-card,
.auth-modal-leave-active .auth-modal-card { transition: transform 0.25s ease; }
.auth-modal-enter-from,
.auth-modal-leave-to { opacity: 0; }
.auth-modal-enter-from .auth-modal-card,
.auth-modal-leave-to .auth-modal-card { transform: scale(0.96) translateY(-8px); }
</style>
