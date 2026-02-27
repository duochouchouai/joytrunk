<template>
  <div class="official-layout">
    <header class="official-header">
      <div class="header-inner">
        <router-link to="/" class="logo">JoyTrunk</router-link>
        <nav class="header-nav">
          <router-link to="/">{{ t('official.nav.home') }}</router-link>
          <a href="/#download" class="nav-link">{{ t('official.nav.download') }}</a>
          <router-link to="/docs">{{ t('official.nav.docs') }}</router-link>
          <router-link to="/pricing">{{ t('official.nav.pricing') }}</router-link>
          <router-link to="/login" class="nav-login">{{ t('official.nav.login') }}</router-link>
          <router-link to="/login?register=1" class="btn primary">{{ t('official.nav.register') }}</router-link>
        </nav>
      </div>
    </header>
    <main class="official-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <footer v-if="showFooter" class="official-footer">
      <div class="footer-inner">
        <span>JoyTrunk 喜象 Agent</span>
        <router-link to="/docs">{{ t('official.nav.docs') }}</router-link>
        <router-link to="/pricing">{{ t('official.nav.pricing') }}</router-link>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { computed } from 'vue'

const { t } = useI18n()
const route = useRoute()
const showFooter = computed(() => route.path === '/' || route.path === '/docs' || route.path === '/pricing')
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
  z-index: 10;
}
.header-inner {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0.75rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.logo {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--jt-primary);
  text-decoration: none;
}
.logo:hover { opacity: 0.9; }
.header-nav {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}
.header-nav a, .nav-link {
  color: var(--jt-text-muted);
  text-decoration: none;
  font-size: 0.9375rem;
}
.header-nav a:hover, .nav-link:hover { color: var(--jt-text); }
.nav-login { margin-right: 0.25rem; }
.btn.primary {
  padding: 0.4rem 0.9rem;
  border-radius: 6px;
  background: var(--jt-primary);
  color: #fff;
  border: none;
  font-size: 0.875rem;
  cursor: pointer;
  text-decoration: none;
}
.btn.primary:hover { opacity: 0.9; }
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
  gap: 1.5rem;
}
.footer-inner a { color: var(--jt-primary); text-decoration: none; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
