<template>
  <div class="about-page">
    <h1 class="page-title">{{ t('official.about.title') }}</h1>
    <p class="intro">{{ t('official.about.intro') }}</p>
    <section class="about-section">
      <h2>{{ t('official.about.product') }}</h2>
      <p>{{ t('official.about.productDesc') }}</p>
    </section>
    <p>
      <router-link to="/" class="link">{{ t('official.nav.home') }}</router-link>
      <span class="dot">·</span>
      <router-link to="/docs" class="link">{{ t('official.nav.docs') }}</router-link>
      <span class="dot">·</span>
      <router-link to="/pricing" class="link">{{ t('official.nav.pricing') }}</router-link>
    </p>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<style scoped>
.about-page { max-width: 560px; margin: 0 auto; padding: 2rem 1.5rem; }
.page-title { margin: 0 0 1rem; font-size: 1.5rem; font-weight: 600; color: var(--jt-text); }
.intro { margin: 0 0 1.5rem; font-size: 0.9375rem; color: var(--jt-text-muted); line-height: 1.6; }
.about-section { margin-bottom: 1.5rem; }
.about-section h2 { margin: 0 0 0.5rem; font-size: 1.125rem; font-weight: 600; color: var(--jt-text); }
.about-section p { margin: 0; font-size: 0.9375rem; color: var(--jt-text-muted); line-height: 1.5; }
.link { color: var(--jt-primary); text-decoration: none; font-size: 0.9375rem; }
.link:hover { text-decoration: underline; }
.dot { margin: 0 0.35rem; color: var(--jt-text-muted); }
</style>
