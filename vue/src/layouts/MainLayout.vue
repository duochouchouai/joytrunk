<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="logo">
        <span class="logo-text">JoyTrunk</span>
      </div>
      <nav class="nav">
        <router-link to="/app/im" class="nav-item" active-class="active">
          <span class="nav-icon">✉</span>
          <span>{{ t('official.im.title') }}</span>
        </router-link>
        <router-link to="/app/overview" class="nav-item" active-class="active">
          <span class="nav-icon">◇</span>
          <span>{{ t('nav.overview') }}</span>
        </router-link>
        <router-link to="/app/chat" class="nav-item" active-class="active">
          <span class="nav-icon">◆</span>
          <span>{{ t('nav.chat') }}</span>
        </router-link>
        <router-link to="/app/employees" class="nav-item" active-class="active">
          <span class="nav-icon">▣</span>
          <span>{{ t('nav.employees') }}</span>
        </router-link>
        <router-link to="/app/settings" class="nav-item" active-class="active">
          <span class="nav-icon">⚙</span>
          <span>{{ t('nav.settings') }}</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <template v-if="token">
          <span class="owner-name">{{ team?.owner?.name || t('nav.owner') }}</span>
          <button type="button" class="btn-text" @click="logout">{{ t('nav.logout') }}</button>
        </template>
        <router-link v-else to="/login" class="btn-text">{{ t('nav.bindAccount') }}</router-link>
      </div>
    </aside>
    <main class="main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, provide, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { api, getToken, clearToken } from '../api'

const { t } = useI18n()
const route = useRoute()
const team = ref(null)
const token = ref(getToken())

async function loadTeam() {
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
provide('refreshTeam', loadTeam)

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
  min-height: 100vh;
  font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
}
.sidebar {
  width: var(--jt-sidebar-w);
  min-width: var(--jt-sidebar-w);
  background: var(--jt-sidebar-bg);
  border-right: 1px solid var(--jt-sidebar-border);
  display: flex;
  flex-direction: column;
}
.logo {
  padding: 1.25rem 1.25rem 0.5rem;
}
.logo-text {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--jt-primary);
  letter-spacing: -0.02em;
}
.nav {
  flex: 1;
  padding: 0.75rem 0;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.5rem 1.25rem;
  color: var(--jt-text-muted);
  text-decoration: none;
  font-size: 0.9375rem;
  transition: color 0.15s, background 0.15s;
}
.nav-item:hover {
  color: var(--jt-text);
  background: var(--jt-bg);
}
.nav-item.active {
  color: var(--jt-primary);
  font-weight: 500;
  background: rgba(15, 118, 110, 0.08);
}
.nav-icon {
  font-size: 0.75rem;
  opacity: 0.9;
}
.sidebar-footer {
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--jt-sidebar-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}
.owner-name {
  font-size: 0.8125rem;
  color: var(--jt-text-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.btn-text {
  background: none;
  border: none;
  color: var(--jt-primary);
  font-size: 0.8125rem;
  cursor: pointer;
  padding: 0.25rem 0;
}
.btn-text:hover { text-decoration: underline; }
.main {
  flex: 1;
  overflow: auto;
  padding: 1.5rem 2rem;
}
.fade-enter-active,
.fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }
</style>
