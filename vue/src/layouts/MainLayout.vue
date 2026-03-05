<template>
  <div class="layout" :class="{ 'layout-mobile': isMobile }">
    <aside v-if="!isMobile" class="sidebar">
      <div class="sidebar-head">
        <router-link to="/" class="logo-link">
          <span class="logo-accent"></span>
          <span class="logo-text">JoyTrunk</span>
        </router-link>
      </div>
      <nav class="nav">
        <router-link to="/app/im" class="nav-item" active-class="active">
          <span class="nav-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          </span>
          <span class="nav-label">{{ t('nav.imChat') }}</span>
        </router-link>
        <router-link to="/app/overview" class="nav-item" active-class="active">
          <span class="nav-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
          </span>
          <span class="nav-label">{{ t('nav.overview') }}</span>
        </router-link>
        <router-link to="/app/token" class="nav-item" active-class="active">
          <span class="nav-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/><circle cx="12" cy="12" r="3"/></svg>
          </span>
          <span class="nav-label">{{ t('nav.token') }}</span>
        </router-link>
        <router-link to="/app/settings" class="nav-item" active-class="active">
          <span class="nav-icon" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
          </span>
          <span class="nav-label">{{ t('nav.settings') }}</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <template v-if="token">
          <div class="user-card">
            <span class="user-avatar">{{ userInitial }}</span>
            <span class="user-name">{{ displayName }}</span>
          </div>
          <button type="button" class="btn-logout" @click="logout">{{ t('nav.logout') }}</button>
        </template>
        <router-link v-else to="/login" class="btn-text">{{ t('nav.bindAccount') }}</router-link>
      </div>
    </aside>
    <main class="main" :class="{ 'main-mobile': isMobile }">
      <div class="main-inner">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
    <!-- 移动端底部 TabBar：聊天、概览、Token、设置 -->
    <nav v-if="isMobile" class="tabbar" role="tablist">
      <router-link to="/app/im" class="tabbar-item" active-class="active" role="tab">
        <span class="tabbar-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        </span>
        <span class="tabbar-label">{{ t('nav.imChat') }}</span>
      </router-link>
      <router-link to="/app/overview" class="tabbar-item" active-class="active" role="tab">
        <span class="tabbar-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
        </span>
        <span class="tabbar-label">{{ t('nav.overview') }}</span>
      </router-link>
      <router-link to="/app/token" class="tabbar-item" active-class="active" role="tab">
        <span class="tabbar-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/><circle cx="12" cy="12" r="3"/></svg>
        </span>
        <span class="tabbar-label">{{ t('nav.token') }}</span>
      </router-link>
      <router-link to="/app/settings" class="tabbar-item" active-class="active" role="tab">
        <span class="tabbar-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
        </span>
        <span class="tabbar-label">{{ t('nav.settings') }}</span>
      </router-link>
    </nav>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, provide, watch, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { api, getToken, clearToken } from '../api'

const isOfficial = import.meta.env.VITE_APP_MODE === 'official'
const MOBILE_BREAKPOINT = 768

const { t } = useI18n()
const route = useRoute()
const team = ref(null)
const me = ref(null)
const token = ref(getToken())
const isMobile = ref(typeof window !== 'undefined' && window.innerWidth <= MOBILE_BREAKPOINT)

function updateMobile() {
  isMobile.value = window.innerWidth <= MOBILE_BREAKPOINT
}

onMounted(() => {
  loadTeam()
  window.addEventListener('resize', updateMobile)
})
onUnmounted(() => {
  window.removeEventListener('resize', updateMobile)
})

const displayName = computed(() => {
  if (isOfficial && me.value?.name) return me.value.name
  return team.value?.owner?.name || t('nav.owner')
})

const userInitial = computed(() => {
  const name = (isOfficial && me.value?.name) ? me.value.name : (team.value?.owner?.name || '')
  return name ? String(name).trim().charAt(0).toUpperCase() || '?' : '?'
})

async function loadTeam() {
  if (isOfficial) {
    try {
      me.value = await api.users.me()
    } catch {
      me.value = null
    }
    return
  }
  try {
    team.value = await api.teams.current()
  } catch {
    team.value = null
  }
}

function logout() {
  clearToken()
  token.value = null
  window.location.href = '/login'
}

provide('team', team)
provide('me', me)
provide('refreshTeam', loadTeam)
provide('isMobile', isMobile)

watch(() => route.path, () => {
  token.value = getToken()
}, { immediate: true })

onMounted(() => {
  loadTeam()
})
</script>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  min-height: 100vh;
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
  overflow: hidden;
}
.sidebar {
  width: var(--jt-sidebar-w);
  min-width: var(--jt-sidebar-w);
  background: var(--jt-sidebar-bg);
  border-right: 1px solid var(--jt-sidebar-border);
  display: flex;
  flex-direction: column;
  box-shadow: 1px 0 0 0 rgba(0, 0, 0, 0.03);
}
[data-theme="dark"] .sidebar {
  box-shadow: 1px 0 0 0 rgba(255, 255, 255, 0.04);
}

.sidebar-head {
  padding: 1.25rem 1rem 1rem;
  border-bottom: 1px solid var(--jt-sidebar-border);
}
.logo-link {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  text-decoration: none;
  color: inherit;
}
.logo-link:hover .logo-text { opacity: 0.9; }
.logo-accent {
  width: 4px;
  height: 24px;
  border-radius: 2px;
  background: var(--jt-primary);
  flex-shrink: 0;
}
.logo-text {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--jt-primary);
  letter-spacing: -0.03em;
  line-height: 1.2;
}

.nav {
  flex: 1;
  padding: 0.75rem 0.5rem;
  overflow-y: auto;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.85rem;
  margin-bottom: 2px;
  color: var(--jt-text-muted);
  text-decoration: none;
  font-size: 0.9375rem;
  font-weight: 500;
  border-radius: 10px;
  transition: color 0.2s ease, background 0.2s ease;
}
.nav-item:hover {
  color: var(--jt-text);
  background: color-mix(in srgb, var(--jt-primary) 8%, transparent);
}
.nav-item.active {
  color: var(--jt-primary);
  background: color-mix(in srgb, var(--jt-primary) 12%, transparent);
  font-weight: 600;
}
.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  opacity: 0.85;
}
.nav-item.active .nav-icon { opacity: 1; }
.nav-icon svg { width: 100%; height: 100%; }
.nav-label { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.sidebar-footer {
  padding: 0.85rem 1rem;
  border-top: 1px solid var(--jt-sidebar-border);
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  background: color-mix(in srgb, var(--jt-primary) 3%, transparent);
}
.user-card {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.5rem 0.6rem;
  border-radius: 10px;
  background: var(--jt-card-bg);
  border: 1px solid var(--jt-sidebar-border);
}
.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--jt-primary);
  color: #fff;
  font-size: 0.8125rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  line-height: 1;
}
.user-name {
  font-size: 0.8125rem;
  color: var(--jt-text);
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}
.btn-logout {
  padding: 0.4rem 0.6rem;
  font-size: 0.8125rem;
  color: var(--jt-primary);
  background: none;
  border: none;
  cursor: pointer;
  text-align: left;
  border-radius: 6px;
  transition: background 0.2s ease;
}
.btn-logout:hover {
  background: color-mix(in srgb, var(--jt-primary) 10%, transparent);
  text-decoration: none;
}
.btn-text {
  padding: 0.5rem 0.6rem;
  font-size: 0.8125rem;
  color: var(--jt-primary);
  text-decoration: none;
  border-radius: 6px;
  transition: background 0.2s ease;
}
.btn-text:hover { background: color-mix(in srgb, var(--jt-primary) 10%, transparent); }

.main {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: auto;
  padding: 1.5rem 2rem;
  background: var(--jt-bg);
}
.main-inner {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.main-inner > * {
  flex: 1;
  min-height: 0;
}
.main-mobile {
  padding: 0;
  padding-bottom: env(safe-area-inset-bottom, 0);
  min-height: 100vh;
  min-height: 100dvh;
}
.tabbar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: calc(56px + env(safe-area-inset-bottom, 0));
  padding-bottom: env(safe-area-inset-bottom, 0);
  display: flex;
  align-items: flex-start;
  justify-content: space-around;
  background: var(--jt-card-bg);
  border-top: 1px solid var(--jt-border);
  z-index: 100;
  flex-shrink: 0;
}
.tabbar-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: 6px 4px 10px;
  color: var(--jt-text-muted);
  text-decoration: none;
  font-size: 0.65rem;
  font-weight: 500;
  min-width: 0;
  transition: color 0.2s;
}
.tabbar-item.active {
  color: var(--jt-primary);
  font-weight: 600;
}
.tabbar-icon {
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  opacity: 0.9;
}
.tabbar-item.active .tabbar-icon {
  opacity: 1;
}
.tabbar-icon svg {
  width: 100%;
  height: 100%;
}
.tabbar-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
.layout-mobile .main {
  padding-bottom: calc(56px + env(safe-area-inset-bottom, 0));
}
.fade-enter-active,
.fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }
</style>
