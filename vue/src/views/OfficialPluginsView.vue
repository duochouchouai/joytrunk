<template>
  <div class="plugins-page">
    <section class="hero">
      <h1 class="plugins-title">{{ t('official.plugins.title') }}</h1>
      <p class="plugins-desc">{{ t('official.plugins.desc') }}</p>
    </section>
    <section class="plugins-list">
      <p class="coming-soon">{{ t('official.plugins.comingSoon') }}</p>
    </section>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
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
  background: var(--jt-card-bg);
  border: 1px solid var(--jt-border);
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}
.coming-soon {
  text-align: center;
  color: var(--jt-text-muted);
  font-size: 0.9375rem;
  margin: 0;
}
</style>
