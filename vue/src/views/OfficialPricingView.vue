<template>
  <div class="pricing-page">
    <h1 class="page-title">{{ t('official.pricing.title') }}</h1>
    <div class="card">
      <p class="para">{{ t('official.pricing.default') }}</p>
      <p class="para">{{ t('official.pricing.custom') }}</p>
      <p class="para muted">{{ t('official.pricing.details') }}</p>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>

<style scoped>
.pricing-page { max-width: 560px; margin: 0 auto; padding: 2rem 1.5rem; }
.page-title { margin: 0 0 1rem; font-size: 1.5rem; font-weight: 600; color: var(--jt-text); }
.card {
  background: var(--jt-card-bg);
  border: 1px solid var(--jt-border);
  border-radius: var(--jt-radius);
  padding: 1.25rem 1.5rem;
}
.para { margin: 0 0 0.75rem; font-size: 0.9375rem; color: var(--jt-text); }
.para.muted { color: var(--jt-text-muted); }
</style>
