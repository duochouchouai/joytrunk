<template>
  <div class="docs-page">
    <h1 class="page-title">{{ t('official.docs.title') }}</h1>
    <p class="intro">{{ t('official.docs.intro') }}</p>
    <p class="hint">{{ t('official.docs.openCli') }}</p>
    <p>
      <a :href="docsUrl" target="_blank" rel="noopener" class="btn primary">{{ t('official.docs.linkText') }}</a>
    </p>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { computed } from 'vue'

const { t } = useI18n()
const docsUrl = computed(() => import.meta.env.VITE_DOCS_URL || 'https://joytrunk.com/docs')
</script>

<style scoped>
.docs-page { max-width: 560px; margin: 0 auto; padding: 2rem 1.5rem; }
.page-title { margin: 0 0 1rem; font-size: 1.5rem; font-weight: 600; color: var(--jt-text); }
.intro, .hint { margin: 0 0 0.75rem; font-size: 0.9375rem; color: var(--jt-text-muted); }
.btn.primary {
  display: inline-block;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  background: var(--jt-primary);
  color: #fff;
  text-decoration: none;
  font-size: 0.9375rem;
}
.btn.primary:hover { opacity: 0.9; }
</style>
