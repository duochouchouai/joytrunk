<template>
  <div class="plugins-page">
    <section class="hero">
      <h1 class="plugins-title">{{ t('official.plugins.title') }}</h1>
      <p class="plugins-desc">{{ t('official.plugins.desc') }}</p>
    </section>
    <section class="plugins-list">
      <div v-for="(plugin, index) in pluginList" :key="index" class="plugin-card">
        <span class="plugin-icon" aria-hidden="true">{{ plugin.icon }}</span>
        <div class="plugin-body">
          <h3 class="plugin-name">{{ plugin.name }}</h3>
          <p class="plugin-desc">{{ plugin.desc }}</p>
          <button type="button" class="plugin-btn" disabled>
            {{ t('official.plugins.comingSoon') }}
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { computed } from 'vue'
import zh from '../i18n/locales/zh'
import en from '../i18n/locales/en'

const localeMessages = { zh, en }

const { locale, t } = useI18n()

const pluginList = computed(() => {
  const list = localeMessages[locale.value]?.official?.plugins?.list
  return Array.isArray(list) ? list : []
})
</script>

<style scoped>
.plugins-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 3rem 1.5rem 4rem;
}
.hero {
  text-align: center;
  margin-bottom: 2.5rem;
}
.plugins-title {
  font-size: 2rem;
  font-weight: 600;
  color: var(--jt-text);
  margin: 0 0 0.75rem;
  letter-spacing: -0.02em;
}
.plugins-desc {
  font-size: 1.0625rem;
  color: var(--jt-text-muted);
  margin: 0;
  line-height: 1.5;
}
.plugins-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.25rem;
  background: transparent;
  border: none;
  padding: 0;
  box-shadow: none;
}
.plugin-card {
  display: flex;
  gap: 1rem;
  padding: 1.25rem;
  background: var(--jt-card-bg);
  border: 1px solid var(--jt-border);
  border-radius: 14px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  transition: border-color 0.2s, box-shadow 0.2s;
}
.plugin-card:hover {
  border-color: color-mix(in srgb, var(--jt-primary) 30%, var(--jt-border));
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}
.plugin-icon {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.75rem;
  background: color-mix(in srgb, var(--jt-primary) 10%, transparent);
  border-radius: 12px;
  line-height: 1;
}
.plugin-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.plugin-name {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--jt-text);
  letter-spacing: -0.01em;
}
.plugin-desc {
  margin: 0;
  font-size: 0.875rem;
  color: var(--jt-text-muted);
  line-height: 1.45;
  flex: 1;
}
.plugin-btn {
  align-self: flex-start;
  margin-top: 0.25rem;
  padding: 0.4rem 0.85rem;
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--jt-text-muted);
  background: var(--jt-bg);
  border: 1px solid var(--jt-border);
  border-radius: 8px;
  cursor: not-allowed;
  font-family: inherit;
}
.coming-soon {
  text-align: center;
  color: var(--jt-text-muted);
  font-size: 0.9375rem;
  margin: 0;
}
</style>
