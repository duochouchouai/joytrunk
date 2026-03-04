<template>
  <div class="landing">
    <section class="hero">
      <h1 class="hero-title">
        <span class="hero-line1">{{ t('official.landing.title') }}</span>
        <span class="hero-line2 accent">{{ t('official.landing.titleSuffix') }}</span>
      </h1>
      <p class="hero-tagline">{{ t('official.landing.tagline') }}</p>
      <ul class="hero-summary">
        <li>{{ t('official.landing.heroPoint1') }}</li>
        <li>{{ t('official.landing.heroPoint2') }}</li>
      </ul>
      <div class="hero-actions">
        <a href="#download" class="btn primary">{{ t('official.landing.ctaPrimary') }}</a>
        <router-link to="/docs" class="btn secondary">{{ t('official.landing.ctaSecondary') }}</router-link>
      </div>
    </section>

    <section class="features">
      <h2 class="section-title">{{ t('official.landing.sectionFeatures') }}</h2>
      <div class="feature-grid">
        <div class="feature-card">
          <span class="feature-icon" aria-hidden="true" v-html="iconHome"></span>
          <h3>{{ t('official.landing.feature1Title') }}</h3>
          <p>{{ t('official.landing.feature1Desc') }}</p>
        </div>
        <div class="feature-card">
          <span class="feature-icon" aria-hidden="true" v-html="iconTeam"></span>
          <h3>{{ t('official.landing.feature2Title') }}</h3>
          <p>{{ t('official.landing.feature2Desc') }}</p>
        </div>
        <div class="feature-card">
          <span class="feature-icon" aria-hidden="true" v-html="iconMessage"></span>
          <h3>{{ t('official.landing.feature3Title') }}</h3>
          <p>{{ t('official.landing.feature3Desc') }}</p>
        </div>
        <div class="feature-card">
          <span class="feature-icon" aria-hidden="true" v-html="iconInstall"></span>
          <h3>{{ t('official.landing.feature4Title') }}</h3>
          <p>{{ t('official.landing.feature4Desc') }}</p>
        </div>
      </div>
    </section>

    <section id="download" class="download">
      <h2 class="section-title">{{ t('official.landing.sectionDownload') }}</h2>

      <div class="download-method download-packages">
        <span class="download-badge">01</span>
        <h3 class="download-method-title">{{ t('official.landing.downloadMethodPackages') }}</h3>
        <p class="download-method-desc">{{ t('official.landing.downloadMethodPackagesDesc') }}</p>
        <div class="download-platforms">
          <a :href="downloadUrlWindows" class="download-platform-btn" target="_blank" rel="noopener">
            <span class="platform-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16" rx="2"/><path d="M4 9h16M9 4v16"/></svg>
            </span>
            Windows
          </a>
          <a :href="downloadUrlMac" class="download-platform-btn" target="_blank" rel="noopener">
            <span class="platform-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="3" width="16" height="14" rx="2" ry="2"/><path d="M8 21h8M12 17v4"/></svg>
            </span>
            macOS
          </a>
          <a :href="downloadUrlLinux" class="download-platform-btn" target="_blank" rel="noopener">
            <span class="platform-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/></svg>
            </span>
            Linux
          </a>
          <a :href="downloadUrlAndroid" class="download-platform-btn" target="_blank" rel="noopener">
            <span class="platform-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 6h-1V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2H7a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2z"/><path d="M9 11h6M9 15h6"/></svg>
            </span>
            Android
          </a>
        </div>
      </div>

      <div class="download-method download-cli">
        <span class="download-badge">02</span>
        <h3 class="download-method-title">{{ t('official.landing.downloadMethodCLI') }}</h3>
        <div class="download-window">
          <div class="download-window-header">
            <div class="window-dots">
              <span class="dot dot-red"></span>
              <span class="dot dot-yellow"></span>
              <span class="dot dot-green"></span>
            </div>
          </div>
          <div class="download-window-body">
            <div class="download-code-wrap">
              <pre class="download-code"><code><span class="code-prompt">$</span> pip install joytrunk
<span class="code-prompt">$</span> joytrunk onboard</code></pre>
              <button type="button" class="download-copy" :title="t('official.landing.downloadCopy')" @click="copyCommand">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                <span v-if="copyDone" class="copy-done">{{ t('official.landing.downloadCopied') }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="follow-us">
      <h2 class="section-title">{{ t('official.landing.sectionFollowUs') }}</h2>
      <div class="follow-links">
        <a :href="followUrlGitHub" class="follow-link" target="_blank" rel="noopener noreferrer" :aria-label="t('official.landing.followGitHub')">
          <span class="follow-icon follow-icon-github" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
          </span>
          <span class="follow-label">{{ t('official.landing.followGitHub') }}</span>
        </a>
        <a :href="followUrlDouyin" class="follow-link" target="_blank" rel="noopener noreferrer" :aria-label="t('official.landing.followDouyin')">
          <span class="follow-icon follow-icon-douyin" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/></svg>
          </span>
          <span class="follow-label">{{ t('official.landing.followDouyin') }}</span>
        </a>
        <a :href="followUrlBilibili" class="follow-link" target="_blank" rel="noopener noreferrer" :aria-label="t('official.landing.followBilibili')">
          <span class="follow-icon follow-icon-bilibili" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M17.813 4.653h.854c.876 0 1.586.71 1.586 1.586v10.28c0 .876-.71 1.586-1.586 1.586H5.333c-.876 0-1.586-.71-1.586-1.586V6.24c0-.876.71-1.586 1.586-1.586h.855V3.067H5.333A3.333 3.333 0 0 0 2 6.4v10.267A3.333 3.333 0 0 0 5.333 20h13.334A3.333 3.333 0 0 0 22 16.667V6.4a3.333 3.333 0 0 0-3.333-3.333h-1.334V4.653zM14.507 12l-3.84 2.227V9.773L14.507 12zM6.667 6.4v11.2h10.666V6.4H6.667z"/></svg>
          </span>
          <span class="follow-label">{{ t('official.landing.followBilibili') }}</span>
        </a>
        <a :href="followUrlXiaohongshu" class="follow-link" target="_blank" rel="noopener noreferrer" :aria-label="t('official.landing.followXiaohongshu')">
          <span class="follow-icon follow-icon-xiaohongshu" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/><path d="M8 7h8M8 11h8"/></svg>
          </span>
          <span class="follow-label">{{ t('official.landing.followXiaohongshu') }}</span>
        </a>
        <a :href="'mailto:' + followEmailAddress" class="follow-link" :aria-label="t('official.landing.followEmail')">
          <span class="follow-icon follow-icon-email" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><path d="M22 6l-10 7L2 6"/></svg>
          </span>
          <span class="follow-label">{{ t('official.landing.followEmail') }}</span>
        </a>
      </div>
    </section>

    <footer class="landing-footer">
      <div class="footer-inner">
        <router-link to="/" class="footer-logo">
          <span class="footer-logo-line1">{{ t('official.landing.title') }}</span>
          <span class="footer-logo-line2">{{ t('official.landing.titleSuffix') }}</span>
        </router-link>
        <nav class="footer-nav">
          <router-link to="/">{{ t('official.landing.footerProduct') }}</router-link>
          <router-link to="/docs">{{ t('official.landing.footerDocs') }}</router-link>
          <router-link to="/pricing">{{ t('official.landing.footerPricing') }}</router-link>
          <router-link to="/about">{{ t('official.nav.about') }}</router-link>
          <span class="footer-legal">{{ t('official.landing.footerLegal') }}</span>
        </nav>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { ref } from 'vue'
import homeSvg from '../assets/home-svgrepo-com.svg?raw'
import teamSvg from '../assets/team-svgrepo-com.svg?raw'
import messageSvg from '../assets/message-2-svgrepo-com.svg?raw'
import installSvg from '../assets/install-svgrepo-com.svg?raw'

const { t } = useI18n()

const copyDone = ref(false)
const installCommand = 'pip install joytrunk\njoytrunk onboard'

// 安装包下载链接（可后续在环境或配置中替换）
const downloadUrlWindows = ref('#')
const downloadUrlMac = ref('#')
const downloadUrlLinux = ref('#')
const downloadUrlAndroid = ref('#')

// 关注我们链接（可后续替换为实际地址）
const followUrlGitHub = ref('https://github.com')
const followUrlDouyin = ref('#')
const followUrlBilibili = ref('https://www.bilibili.com')
const followUrlXiaohongshu = ref('https://www.xiaohongshu.com')
const followEmailAddress = ref('contact@example.com')

async function copyCommand() {
  try {
    await navigator.clipboard.writeText(installCommand)
    copyDone.value = true
    setTimeout(() => { copyDone.value = false }, 2000)
  } catch {
    copyDone.value = false
  }
}

function useCurrentColor(svgString) {
  return svgString
    .replace(/stroke="#[^"]+"/g, 'stroke="currentColor"')
    .replace(/fill="#[^"]+"/g, (m) => (m === 'fill="none"' ? m : 'fill="currentColor"'))
}

const iconHome = useCurrentColor(homeSvg)
const iconTeam = useCurrentColor(teamSvg)
const iconMessage = useCurrentColor(messageSvg)
const iconInstall = useCurrentColor(installSvg)
</script>

<style scoped>
.landing { font-family: 'Segoe UI', system-ui, sans-serif; }
.hero {
  text-align: center;
  padding: 6rem 1.5rem 9rem;
  max-width: 800px;
  margin: 0 auto;
  min-height: 50vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.hero-title {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 0 0 0.75rem;
  font-size: clamp(2rem, 5vw, 3rem);
  font-weight: 700;
  color: var(--jt-text);
  line-height: 1.2;
}
.hero-line1 { display: block; }
.hero-line2 { display: block; font-size: 0.85em; margin-top: 0.15em; }
.hero-line2.accent { color: var(--jt-primary); }
.hero-line3 { display: block; font-size: 0.55em; font-weight: 500; color: var(--jt-text-muted); margin-top: 0.35em; }
.hero-tagline { margin: 0 0 1rem; font-size: 1.25rem; color: var(--jt-text-muted); line-height: 1.4; }
.hero-summary {
  margin: 2.5rem auto 2.5rem;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  max-width: 520px;
  text-align: center;
}
.hero-summary li {
  position: relative;
  margin: 0;
  padding: 0 1rem;
  font-size: 1.125rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  line-height: 1.55;
  color: var(--jt-text);
  font-family: Georgia, 'STSong', 'SimSun', serif;
}
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
.btn.outline:hover { background: rgba(37, 99, 235, 0.08); }

.features { padding: 3.5rem 1.5rem; background: var(--jt-bg); }
.section-title {
  text-align: center;
  margin: 0 0 2.25rem;
  font-size: 1.125rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--jt-text-muted);
  text-transform: uppercase;
}
.feature-grid {
  max-width: 960px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.25rem;
}
@media (max-width: 900px) {
  .feature-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 480px) {
  .feature-grid { grid-template-columns: 1fr; }
}
.feature-card {
  background: var(--jt-card-bg);
  border: 1px solid var(--jt-border);
  border-radius: 12px;
  padding: 1.35rem 1.25rem;
  text-align: center;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.feature-card:hover {
  border-color: var(--jt-primary);
  box-shadow: 0 4px 16px rgba(37, 99, 235, 0.08);
}
.feature-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  margin: 0 auto 0.75rem;
  color: var(--jt-primary);
}
.feature-icon :deep(svg) {
  width: 100%;
  height: 100%;
  opacity: 0.92;
}
.feature-card:hover .feature-icon {
  color: var(--jt-primary);
  opacity: 1;
}
.feature-card h3 {
  margin: 0 0 0.4rem;
  font-size: 0.9375rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  color: var(--jt-text);
}
.feature-card p {
  margin: 0;
  font-size: 0.8125rem;
  line-height: 1.5;
  color: var(--jt-text-muted);
}

.download { padding: 3rem 1.5rem; max-width: 680px; margin: 0 auto; text-align: center; }
.download .section-title { text-align: center; margin-bottom: 2rem; }

.download-method {
  position: relative;
  margin-bottom: 2rem;
  padding: 1.75rem 1.5rem;
  background: var(--jt-card-bg);
  border: 1px solid var(--jt-border);
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.25s ease, border-color 0.2s ease;
}
.download-method:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border-color: var(--jt-border);
}
[data-theme="dark"] .download-method {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
}
[data-theme="dark"] .download-method:hover {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.download-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  margin-bottom: 1rem;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--jt-primary);
  background: var(--jt-bg);
  background: color-mix(in srgb, var(--jt-primary) 14%, transparent);
  border: 1px solid color-mix(in srgb, var(--jt-primary) 25%, transparent);
  border-radius: 10px;
  line-height: 1;
}

.download-method-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--jt-text);
  margin: 0 0 0.5rem;
  text-align: center;
  letter-spacing: -0.01em;
}
.download-method-desc {
  font-size: 0.875rem;
  color: var(--jt-text-muted);
  margin: 0 0 1.25rem;
  text-align: center;
  line-height: 1.55;
  max-width: 420px;
  margin-left: auto;
  margin-right: auto;
}

.download-platforms {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: center;
}
.download-platform-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.65rem 1.25rem;
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--jt-text);
  background: var(--jt-bg);
  border: 1px solid var(--jt-border);
  border-radius: 12px;
  text-decoration: none;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}
.download-platform-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: var(--jt-primary);
  color: var(--jt-primary);
}
[data-theme="dark"] .download-platform-btn:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}
.platform-icon {
  display: inline-flex;
  width: 18px;
  height: 18px;
  color: var(--jt-text-muted);
  transition: color 0.2s ease;
}
.download-platform-btn:hover .platform-icon {
  color: var(--jt-primary);
}
.platform-icon svg {
  width: 100%;
  height: 100%;
}

.download-cli .download-method-title { margin-bottom: 1rem; }

.download-window {
  background: var(--jt-bg);
  border: 1px solid var(--jt-border);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.5);
  transition: box-shadow 0.2s ease;
}
[data-theme="dark"] .download-window {
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
}
.download-window-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.65rem 1rem;
  background: var(--jt-card-bg);
  border-bottom: 1px solid var(--jt-border);
}
.window-dots { display: flex; gap: 6px; }
.window-dots .dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.dot-red { background: #ff5f57; }
.dot-yellow { background: #febc2e; }
.dot-green { background: #28c840; }

.download-window-body { padding: 1rem; }

.download-code-wrap {
  position: relative;
  background: #f8f9fa;
  border: 1px solid var(--jt-border);
  border-radius: 10px;
  padding: 1rem 1.25rem;
  padding-right: 2.75rem;
  text-align: left;
  transition: background 0.2s ease;
}
[data-theme="dark"] .download-code-wrap { background: rgba(0, 0, 0, 0.25); }
.download-code {
  margin: 0;
  font-size: 0.9375rem;
  font-family: ui-monospace, 'Cascadia Code', 'SF Mono', 'Consolas', monospace;
  line-height: 1.7;
  overflow-x: auto;
  color: var(--jt-text);
  text-align: left;
  letter-spacing: 0.01em;
}
.download-code .code-prompt { color: var(--jt-primary); user-select: none; font-weight: 600; }
.download-copy {
  position: absolute;
  top: 0.75rem;
  right: 0.75rem;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--jt-text-muted);
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease;
}
.download-copy:hover { background: var(--jt-border); color: var(--jt-text); }
.download-copy .copy-done {
  position: absolute;
  right: 100%;
  margin-right: 0.5rem;
  font-size: 0.75rem;
  color: var(--jt-primary);
  white-space: nowrap;
  font-weight: 500;
}

.follow-us {
  padding: 3rem 1.5rem;
  max-width: 680px;
  margin: 0 auto;
  text-align: center;
}
.follow-us .section-title {
  margin-bottom: 1.5rem;
  text-align: center;
}
.follow-links {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: center;
  align-items: center;
}
.follow-link {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1.1rem;
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--jt-text);
  background: var(--jt-card-bg);
  border: 1px solid var(--jt-border);
  border-radius: 12px;
  text-decoration: none;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease, color 0.2s ease;
}
.follow-link:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-color: var(--jt-primary);
  color: var(--jt-primary);
}
[data-theme="dark"] .follow-link:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}
.follow-icon {
  display: inline-flex;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: var(--jt-text-muted);
  transition: color 0.2s ease;
}
.follow-link:hover .follow-icon {
  color: var(--jt-primary);
}
.follow-icon svg {
  width: 100%;
  height: 100%;
}
.follow-label {
  white-space: nowrap;
}

.landing-footer { border-top: 1px solid var(--jt-border); padding: 1.5rem 1.5rem; background: var(--jt-card-bg); }
.footer-inner { max-width: 960px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1rem; }
.footer-logo {
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--jt-primary);
  text-decoration: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  line-height: 1.3;
}
.footer-logo-line1 { font-size: 1em; }
.footer-logo-line2 { font-size: 0.7em; letter-spacing: 0.02em; }
.footer-nav { display: flex; align-items: center; gap: 1.25rem; font-size: 0.875rem; }
.footer-nav a { color: var(--jt-text-muted); text-decoration: none; }
.footer-nav a:hover { color: var(--jt-text); }
.footer-legal { color: var(--jt-text-muted); }
</style>
