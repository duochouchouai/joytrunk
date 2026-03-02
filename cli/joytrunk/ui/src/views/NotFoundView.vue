<template>
  <div class="not-found">
    <h1 class="title">{{ t('notFound.title') }}</h1>
    <p class="hint">{{ t('notFound.hint') }}</p>
    <router-link to="/" class="link">{{ t('notFound.backHome') }}</router-link>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>

<style scoped>
.not-found {
  padding: 2rem;
  text-align: center;
}
.title { font-size: 1.25rem; font-weight: 600; margin: 0 0 0.5rem; }
.hint { color: var(--jt-text-muted); font-size: 0.9375rem; margin: 0 0 1rem; }
.link { color: var(--jt-primary); text-decoration: none; font-size: 0.9375rem; }
.link:hover { text-decoration: underline; }
</style>
