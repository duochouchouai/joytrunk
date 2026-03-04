<template>
  <div class="official-layout">
    <header class="official-header">
      <div class="header-inner">
        <router-link to="/" class="logo">
          <span class="logo-line1">{{ t('official.landing.title') }}</span>
          <span class="logo-line2 accent">{{ t('official.landing.titleSuffix') }}</span>
        </router-link>

        <!-- Desktop nav: 产品、下载、文档、定价、关于 | 控制台、头像 -->
        <nav class="header-nav">
          <div class="nav-left">
            <template v-if="showMainNav">
              <router-link to="/">{{ t('official.nav.home') }}</router-link>
              <a href="/#download" class="nav-link">{{ t('official.nav.download') }}</a>
            </template>
            <router-link to="/plugins">{{ t('official.nav.plugins') }}</router-link>
            <router-link to="/docs">{{ t('official.nav.docs') }}</router-link>
            <template v-if="showMainNav">
              <router-link to="/pricing">{{ t('official.nav.pricing') }}</router-link>
              <router-link to="/about">{{ t('official.nav.about') }}</router-link>
            </template>
          </div>
          <div class="nav-right">
            <div class="lang-switch" role="group" :aria-label="t('official.nav.language')">
              <button
                type="button"
                class="lang-btn"
                :class="{ active: locale === 'zh' }"
                @click="setLocale('zh')"
              >
                中文
              </button>
              <span class="lang-sep">/</span>
              <button
                type="button"
                class="lang-btn"
                :class="{ active: locale === 'en' }"
                @click="setLocale('en')"
              >
                English
              </button>
            </div>
            <template v-if="isLoggedIn">
              <router-link to="/app" class="btn primary btn-console">{{ t('official.nav.console') }}</router-link>
              <div
                class="avatar-wrap"
                ref="avatarWrapRef"
                @mouseenter="avatarOpen = true"
                @mouseleave="avatarOpen = false"
              >
                <button
                  type="button"
                  class="avatar-btn"
                  :aria-expanded="avatarOpen"
                  aria-haspopup="true"
                  @click.stop="avatarOpen = !avatarOpen"
                >
                  <span class="avatar-circle" :title="t('official.nav.profile')">
                    {{ userInitial }}
                  </span>
                </button>
                <Transition name="dropdown">
                  <div v-show="avatarOpen" class="avatar-dropdown" role="menu">
                    <router-link
                      to="/app/settings"
                      class="dropdown-item"
                      role="menuitem"
                      @click="avatarOpen = false"
                    >
                      {{ t('official.nav.settings') }}
                    </router-link>
                    <button
                      type="button"
                      class="dropdown-item dropdown-item-danger"
                      role="menuitem"
                      @click="doLogout"
                    >
                      {{ t('official.nav.logout') }}
                    </button>
                  </div>
                </Transition>
              </div>
            </template>
            <template v-else>
              <button type="button" class="nav-link nav-btn" @click="openAuth('login')">{{ t('official.nav.login') }}</button>
              <button type="button" class="btn primary" @click="openAuth('register')">{{ t('official.nav.register') }}</button>
            </template>
          </div>
        </nav>

        <!-- Mobile: hamburger -->
        <button
          type="button"
          class="hamburger"
          :aria-expanded="mobileOpen"
          aria-label="菜单"
          @click="mobileOpen = !mobileOpen"
        >
          <span class="hamburger-bar"></span>
          <span class="hamburger-bar"></span>
          <span class="hamburger-bar"></span>
        </button>
      </div>

      <!-- Mobile menu overlay -->
      <Transition name="mobile">
        <div v-show="mobileOpen" class="mobile-overlay" @click="mobileOpen = false">
          <nav class="mobile-nav" @click.stop>
            <template v-if="showMainNav">
              <router-link to="/" @click="mobileOpen = false">{{ t('official.nav.home') }}</router-link>
              <a href="/#download" @click="mobileOpen = false">{{ t('official.nav.download') }}</a>
            </template>
            <router-link to="/plugins" @click="mobileOpen = false">{{ t('official.nav.plugins') }}</router-link>
            <router-link to="/docs" @click="mobileOpen = false">{{ t('official.nav.docs') }}</router-link>
            <template v-if="showMainNav">
              <router-link to="/pricing" @click="mobileOpen = false">{{ t('official.nav.pricing') }}</router-link>
              <router-link to="/about" @click="mobileOpen = false">{{ t('official.nav.about') }}</router-link>
            </template>
            <template v-if="isLoggedIn">
              <router-link to="/app" class="mobile-console" @click="mobileOpen = false">{{ t('official.nav.console') }}</router-link>
              <router-link to="/app/settings" @click="mobileOpen = false">{{ t('official.nav.settings') }}</router-link>
              <button type="button" class="mobile-logout" @click="doLogout">
                {{ t('official.nav.logout') }}
              </button>
            </template>
            <template v-else>
              <button type="button" class="mobile-auth-btn" @click="openAuth('login'); mobileOpen = false">{{ t('official.nav.login') }}</button>
              <button type="button" class="mobile-auth-btn primary" @click="openAuth('register'); mobileOpen = false">{{ t('official.nav.register') }}</button>
            </template>
            <div class="mobile-lang">
              <span class="mobile-lang-label">{{ t('official.nav.language') }}</span>
              <button type="button" class="mobile-lang-btn" :class="{ active: locale === 'zh' }" @click="setLocale('zh'); mobileOpen = false">中文</button>
              <button type="button" class="mobile-lang-btn" :class="{ active: locale === 'en' }" @click="setLocale('en'); mobileOpen = false">English</button>
            </div>
          </nav>
        </div>
      </Transition>
    </header>

    <main class="official-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <AuthModal
      :show="showAuthModal"
      :mode="authMode"
      @close="showAuthModal = false"
      @update:mode="authMode = $event"
      @success="onAuthSuccess"
    />

    <footer v-if="showFooter" class="official-footer">
      <div class="footer-inner">
        <span>JoyTrunk 快乐象鼻 Agent</span>
        <router-link to="/docs">{{ t('official.nav.docs') }}</router-link>
        <router-link to="/plugins">{{ t('official.nav.plugins') }}</router-link>
        <router-link to="/pricing">{{ t('official.nav.pricing') }}</router-link>
        <router-link to="/about">{{ t('official.nav.about') }}</router-link>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { getToken, clearToken, api } from '../api'
import { setLocale } from '../i18n'
import AuthModal from '../components/AuthModal.vue'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const showFooter = computed(() => ['/docs', '/pricing', '/about', '/plugins'].includes(route.path))
/** 暂时隐藏导航：产品、下载、定价、关于（改为 true 可恢复） */
const showMainNav = ref(false)

const loggedInRef = ref(!!getToken())
const isLoggedIn = computed(() => loggedInRef.value)

const avatarOpen = ref(false)
const mobileOpen = ref(false)
const avatarWrapRef = ref(null)
const userInitial = ref('?')
const showAuthModal = ref(false)
const authMode = ref('login')

function openAuth(mode) {
  authMode.value = mode
  showAuthModal.value = true
}

function onAuthSuccess() {
  showAuthModal.value = false
  loggedInRef.value = true
  router.push('/app/im')
}

function doLogout() {
  clearToken()
  loggedInRef.value = false
  avatarOpen.value = false
  mobileOpen.value = false
  router.push('/')
}

function handleClickOutside(e) {
  if (avatarWrapRef.value && !avatarWrapRef.value.contains(e.target)) {
    avatarOpen.value = false
  }
}

onMounted(async () => {
  loggedInRef.value = !!getToken()
  if (getToken()) {
    try {
      const me = await api.users.me()
      const name = me?.name || ''
      userInitial.value = name ? String(name).trim().charAt(0).toUpperCase() || '?' : '?'
    } catch {
      userInitial.value = '?'
    }
  }
  document.addEventListener('click', handleClickOutside)
})
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.official-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: 'Segoe UI', system-ui, sans-serif;
}
.official-header {
  border-bottom: 1px solid var(--jt-border);
  background: var(--jt-card-bg);
  position: sticky;
  top: 0;
  z-index: 50;
}
.header-inner {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0.75rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}
.logo {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--jt-primary);
  text-decoration: none;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  line-height: 1.25;
  align-items: center;
}
.logo:hover { opacity: 0.9; }
.logo-line1 { font-size: 1.1em; }
.logo-line2 { font-size: 0.7em; letter-spacing: 0.02em; }
.logo-line2.accent { color: var(--jt-primary); }

.header-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex: 1;
  gap: 1rem;
}
.nav-left,
.nav-right {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}
.header-nav a,
.nav-link {
  color: var(--jt-text-muted);
  text-decoration: none;
  font-size: 0.9375rem;
  white-space: nowrap;
}
.header-nav a:hover,
.nav-link:hover { color: var(--jt-text); }

.nav-btn {
  background: none;
  border: none;
  font: inherit;
  cursor: pointer;
  padding: 0;
}

.btn.primary {
  padding: 0.4rem 0.9rem;
  border-radius: 6px;
  background: var(--jt-primary);
  color: #fff;
  border: none;
  font-size: 0.875rem;
  cursor: pointer;
  text-decoration: none;
  white-space: nowrap;
}
.btn.primary:hover { opacity: 0.9; }

/* Language switch */
.lang-switch {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}
.lang-btn {
  padding: 0.25rem 0.5rem;
  font-size: 0.8125rem;
  color: var(--jt-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  font-family: inherit;
  border-radius: 4px;
}
.lang-btn:hover { color: var(--jt-text); }
.lang-btn.active { color: var(--jt-primary); font-weight: 500; }
.lang-sep { color: var(--jt-text-muted); font-size: 0.75rem; user-select: none; }

/* Avatar */
.avatar-wrap {
  position: relative;
}
.avatar-btn {
  padding: 0;
  border: none;
  background: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  min-width: 44px;
  min-height: 44px;
}
.avatar-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--jt-primary);
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  flex-shrink: 0;
}
.avatar-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 140px;
  padding: 0.35rem 0;
  background: var(--jt-card-bg);
  border: 1px solid var(--jt-border);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
.dropdown-item {
  display: block;
  width: 100%;
  padding: 0.5rem 1rem;
  text-align: left;
  font-size: 0.875rem;
  color: var(--jt-text);
  text-decoration: none;
  border: none;
  background: none;
  cursor: pointer;
  font-family: inherit;
}
.dropdown-item:hover {
  background: var(--jt-bg);
}
.dropdown-item-danger { color: var(--jt-text-muted); }
.dropdown-item-danger:hover { color: #c00; }

.dropdown-enter-active,
.dropdown-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* Hamburger: hidden on desktop */
.hamburger {
  display: none;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
  width: 40px;
  height: 40px;
  padding: 0;
  border: none;
  background: none;
  cursor: pointer;
  color: var(--jt-text);
}
.hamburger-bar {
  display: block;
  width: 22px;
  height: 2px;
  background: currentColor;
  border-radius: 1px;
}

/* Mobile overlay */
.mobile-overlay {
  position: fixed;
  inset: 0;
  top: 57px;
  background: rgba(0, 0, 0, 0.4);
  z-index: 40;
  overflow-y: auto;
}
.mobile-nav {
  background: var(--jt-card-bg);
  padding: 1rem 1.5rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.mobile-nav a,
.mobile-logout,
.mobile-auth-btn {
  padding: 0.75rem 0;
  font-size: 1rem;
  color: var(--jt-text);
  text-decoration: none;
  border: none;
  background: none;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  border-bottom: 1px solid var(--jt-border);
}
.mobile-auth-btn.primary { color: var(--jt-primary); font-weight: 500; }
.mobile-nav a:last-of-type,
.mobile-nav .mobile-logout,
.mobile-nav .mobile-auth-btn { border-bottom: none; }
.mobile-console {
  color: var(--jt-primary);
  font-weight: 500;
}
.mobile-logout { color: var(--jt-text-muted); }

.mobile-lang {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--jt-border);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.mobile-lang-label { font-size: 0.875rem; color: var(--jt-text-muted); }
.mobile-lang-btn {
  padding: 0.35rem 0.6rem;
  font-size: 0.875rem;
  color: var(--jt-text-muted);
  background: none;
  border: 1px solid var(--jt-border);
  border-radius: 6px;
  cursor: pointer;
  font-family: inherit;
}
.mobile-lang-btn.active { color: var(--jt-primary); border-color: var(--jt-primary); font-weight: 500; }

.mobile-enter-active,
.mobile-leave-active { transition: opacity 0.2s ease; }
.mobile-enter-from,
.mobile-leave-to { opacity: 0; }

@media (max-width: 768px) {
  .header-nav { display: none; }
  .hamburger { display: flex; }
}

.official-main { flex: 1; }
.official-footer {
  border-top: 1px solid var(--jt-border);
  background: var(--jt-card-bg);
  padding: 1rem 1.5rem;
  font-size: 0.875rem;
  color: var(--jt-text-muted);
}
.footer-inner {
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}
.footer-inner a { color: var(--jt-primary); text-decoration: none; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
