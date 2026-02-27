<template>
  <div class="landing">
    <section class="hero">
      <h1 class="hero-title">{{ t('official.landing.title') }}<span class="accent"> {{ t('official.landing.titleSuffix') }}</span></h1>
      <p class="hero-tagline">{{ t('official.landing.tagline') }}</p>
      <div class="hero-actions">
        <a href="#download" class="btn primary">{{ t('official.landing.ctaPrimary') }}</a>
        <router-link to="/docs" class="btn secondary">{{ t('official.landing.ctaSecondary') }}</router-link>
        <router-link to="/login" class="btn outline">{{ t('official.nav.login') }}</router-link>
      </div>
    </section>

    <section class="features">
      <h2 class="section-title">{{ t('official.landing.sectionFeatures') }}</h2>
      <div class="feature-grid">
        <div class="feature-card">
          <div class="feature-icon">◆</div>
          <h3>{{ t('official.landing.feature1Title') }}</h3>
          <p>{{ t('official.landing.feature1Desc') }}</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">◇</div>
          <h3>{{ t('official.landing.feature2Title') }}</h3>
          <p>{{ t('official.landing.feature2Desc') }}</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">▣</div>
          <h3>{{ t('official.landing.feature3Title') }}</h3>
          <p>{{ t('official.landing.feature3Desc') }}</p>
        </div>
      </div>
    </section>

    <section id="download" class="download">
      <h2 class="section-title">{{ t('official.landing.sectionDownload') }}</h2>
      <pre class="code"><code>{{ t('official.landing.installCmd') }}</code></pre>
      <p class="get-started">{{ t('official.landing.getStarted') }}</p>
      <p class="steps">{{ t('official.landing.getStartedSteps') }}</p>
      <div class="download-actions">
        <router-link to="/docs" class="link">{{ t('official.landing.ctaDocs') }}</router-link>
        <span class="dot">·</span>
        <router-link to="/pricing" class="link">{{ t('official.landing.ctaPricing') }}</router-link>
      </div>
    </section>

    <section class="cta">
      <h2 class="section-title">{{ t('official.landing.sectionCta') }}</h2>
      <router-link to="/login" class="btn primary">{{ t('official.nav.register') }}</router-link>
    </section>

    <footer class="landing-footer">
      <div class="footer-inner">
        <router-link to="/" class="footer-logo">JoyTrunk</router-link>
        <nav class="footer-nav">
          <router-link to="/">{{ t('official.landing.footerProduct') }}</router-link>
          <router-link to="/docs">{{ t('official.landing.footerDocs') }}</router-link>
          <router-link to="/pricing">{{ t('official.landing.footerPricing') }}</router-link>
          <span class="footer-legal">{{ t('official.landing.footerLegal') }}</span>
        </nav>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>

<style scoped>
.landing { font-family: 'Segoe UI', system-ui, sans-serif; }
.hero {
  text-align: center;
  padding: 4rem 1.5rem 5rem;
  max-width: 720px;
  margin: 0 auto;
}
.hero-title { margin: 0 0 0.75rem; font-size: clamp(1.75rem, 4vw, 2.5rem); font-weight: 700; color: var(--jt-text); line-height: 1.2; }
.hero-title .accent { color: var(--jt-primary); }
.hero-tagline { margin: 0 0 2rem; font-size: 1.125rem; color: var(--jt-text-muted); }
.hero-actions { display: flex; gap: 0.75rem; justify-content: center; flex-wrap: wrap; }
.btn {
  display: inline-block;
  padding: 0.65rem 1.35rem;
  border-radius: 8px;
  font-size: 0.9375rem;
  font-weight: 500;
  text-decoration: none;
  transition: opacity 0.15s;
}
.btn.primary { background: var(--jt-primary); color: #fff; }
.btn.primary:hover { opacity: 0.92; }
.btn.secondary { border: 1px solid var(--jt-border); color: var(--jt-text); }
.btn.secondary:hover { background: var(--jt-bg); }
.btn.outline { color: var(--jt-primary); border: 1px solid var(--jt-primary); }
.btn.outline:hover { background: rgba(15, 118, 110, 0.08); }

.features { padding: 3rem 1.5rem; background: var(--jt-bg); }
.section-title { text-align: center; margin: 0 0 2rem; font-size: 1.25rem; font-weight: 600; color: var(--jt-text); }
.feature-grid {
  max-width: 960px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.5rem;
}
.feature-card {
  background: var(--jt-card-bg);
  border: 1px solid var(--jt-border);
  border-radius: 12px;
  padding: 1.5rem;
}
.feature-icon { font-size: 1.5rem; color: var(--jt-primary); margin-bottom: 0.5rem; }
.feature-card h3 { margin: 0 0 0.5rem; font-size: 1rem; font-weight: 600; color: var(--jt-text); }
.feature-card p { margin: 0; font-size: 0.875rem; color: var(--jt-text-muted); line-height: 1.5; }

.download { padding: 3rem 1.5rem; max-width: 560px; margin: 0 auto; }
.download .section-title { text-align: left; margin-bottom: 1rem; }
.code {
  background: var(--jt-bg);
  border: 1px solid var(--jt-border);
  border-radius: 8px;
  padding: 0.85rem 1rem;
  font-size: 0.9375rem;
  overflow-x: auto;
}
.code code { font-family: ui-monospace, monospace; }
.get-started { margin: 1.25rem 0 0.25rem; font-size: 0.9375rem; font-weight: 500; color: var(--jt-text); }
.steps { margin: 0 0 1rem; font-size: 0.875rem; color: var(--jt-text-muted); }
.download-actions { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.link { color: var(--jt-primary); text-decoration: none; font-size: 0.9375rem; }
.link:hover { text-decoration: underline; }
.dot { color: var(--jt-text-muted); }

.cta { text-align: center; padding: 3rem 1.5rem; }
.cta .section-title { margin-bottom: 1rem; }

.landing-footer { border-top: 1px solid var(--jt-border); padding: 1.5rem 1.5rem; background: var(--jt-card-bg); }
.footer-inner { max-width: 960px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem; }
.footer-logo { font-size: 1.125rem; font-weight: 600; color: var(--jt-primary); text-decoration: none; }
.footer-nav { display: flex; align-items: center; gap: 1.25rem; font-size: 0.875rem; }
.footer-nav a { color: var(--jt-text-muted); text-decoration: none; }
.footer-nav a:hover { color: var(--jt-text); }
.footer-legal { color: var(--jt-text-muted); }
</style>
