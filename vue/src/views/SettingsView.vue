<template>
  <div class="page" :class="{ 'page-mobile': isMobile }">
    <template v-if="isMobile">
      <MobileTitleBar :title="t('settings.title')" />
      <div class="mobile-content">
        <!-- 上方：头像 + 昵称 -->
        <section class="profile-section">
          <div class="profile-avatar-wrap">
            <div class="profile-avatar">
              <img v-if="displayAvatarUrl" :src="displayAvatarUrl" alt="" class="avatar-img" @error="avatarError = true" />
              <span v-else class="avatar-initial">{{ avatarInitial }}</span>
            </div>
          </div>
          <div class="profile-fields">
            <label class="field-label">{{ t('settings.nickname') }}</label>
            <input
              v-model="nickname"
              type="text"
              class="field-input"
              :placeholder="t('settings.nicknamePlaceholder')"
              maxlength="100"
            />
            <label class="field-label">{{ t('settings.avatar') }}</label>
            <input
              v-model="avatarUrl"
              type="url"
              class="field-input"
              :placeholder="t('settings.avatarPlaceholder')"
              @input="avatarError = false"
            />
          </div>
        </section>
        <section class="prefs-section">
          <h2 class="section-title">{{ t('settings.preferences') }}</h2>
          <div class="prefs-card">
            <div class="pref-row">
              <span class="pref-label">{{ t('settings.language') }}</span>
              <div ref="langDropdownRef" class="dropdown-wrap">
                <button type="button" class="dropdown-trigger" :class="{ open: languageOpen }" @click.stop="languageOpen = !languageOpen">
                  <span class="dropdown-value">{{ currentLanguageLabel }}</span>
                  <span class="dropdown-chevron" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
                  </span>
                </button>
                <Transition name="dropdown">
                  <div v-show="languageOpen" class="dropdown-card" role="listbox">
                    <button
                      v-for="opt in languageOptions"
                      :key="opt.value"
                      type="button"
                      role="option"
                      :aria-selected="locale === opt.value"
                      class="dropdown-option"
                      :class="{ active: locale === opt.value }"
                      @click.stop="chooseLanguage(opt.value)"
                    >
                      <span>{{ opt.label }}</span>
                      <span v-if="locale === opt.value" class="dropdown-check" aria-hidden="true">✓</span>
                    </button>
                  </div>
                </Transition>
              </div>
            </div>
            <div class="pref-row">
              <span class="pref-label">{{ t('settings.theme') }}</span>
              <div ref="themeDropdownRef" class="dropdown-wrap">
                <button type="button" class="dropdown-trigger" :class="{ open: themeOpen }" @click.stop="themeOpen = !themeOpen">
                  <span class="dropdown-value">{{ currentThemeLabel }}</span>
                  <span class="dropdown-chevron" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
                  </span>
                </button>
                <Transition name="dropdown">
                  <div v-show="themeOpen" class="dropdown-card" role="listbox">
                    <button
                      v-for="opt in themeOptions"
                      :key="opt.value"
                      type="button"
                      role="option"
                      :aria-selected="theme === opt.value"
                      class="dropdown-option"
                      :class="{ active: theme === opt.value }"
                      @click.stop="chooseTheme(opt.value)"
                    >
                      <span>{{ opt.label }}</span>
                      <span v-if="theme === opt.value" class="dropdown-check" aria-hidden="true">✓</span>
                    </button>
                  </div>
                </Transition>
              </div>
            </div>
            <div class="pref-row pref-row-toggle">
              <span class="pref-label">{{ t('settings.syncJoytrunkChat') }}</span>
              <button
                type="button"
                class="toggle-btn"
                :class="{ on: syncJoytrunkChat }"
                role="switch"
                :aria-checked="syncJoytrunkChat"
                @click="syncJoytrunkChat = !syncJoytrunkChat"
              >
                <span class="toggle-thumb"></span>
              </button>
            </div>
          </div>
        </section>
        <div class="actions">
          <button type="button" class="btn-save" :disabled="saving" @click="saveProfile">
            <span v-if="saving" class="btn-loading"></span>
            <span v-else>{{ saving ? t('common.loading') : t('settings.save') }}</span>
          </button>
          <p v-if="saveError" class="msg msg-error">{{ saveError }}</p>
          <p v-if="saveSuccess" class="msg msg-success">{{ t('settings.saved') }}</p>
        </div>
      </div>
    </template>
    <template v-else>
      <h1 class="page-title">{{ t('settings.title') }}</h1>

      <!-- 上方：头像 + 昵称 -->
      <section class="profile-section">
      <div class="profile-avatar-wrap">
        <div class="profile-avatar">
          <img v-if="displayAvatarUrl" :src="displayAvatarUrl" alt="" class="avatar-img" @error="avatarError = true" />
          <span v-else class="avatar-initial">{{ avatarInitial }}</span>
        </div>
      </div>
      <div class="profile-fields">
        <label class="field-label">{{ t('settings.nickname') }}</label>
        <input
          v-model="nickname"
          type="text"
          class="field-input"
          :placeholder="t('settings.nicknamePlaceholder')"
          maxlength="100"
        />
        <label class="field-label">{{ t('settings.avatar') }}</label>
        <input
          v-model="avatarUrl"
          type="url"
          class="field-input"
          :placeholder="t('settings.avatarPlaceholder')"
          @input="avatarError = false"
        />
      </div>
    </section>

    <!-- 语言与主题 -->
    <section class="prefs-section">
      <h2 class="section-title">{{ t('settings.preferences') }}</h2>
      <div class="prefs-card">
        <div class="pref-row">
          <span class="pref-label">{{ t('settings.language') }}</span>
          <div ref="langDropdownRef" class="dropdown-wrap">
            <button type="button" class="dropdown-trigger" :class="{ open: languageOpen }" @click.stop="languageOpen = !languageOpen">
              <span class="dropdown-value">{{ currentLanguageLabel }}</span>
              <span class="dropdown-chevron" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
              </span>
            </button>
            <Transition name="dropdown">
              <div v-show="languageOpen" class="dropdown-card" role="listbox">
                <button
                  v-for="opt in languageOptions"
                  :key="opt.value"
                  type="button"
                  role="option"
                  :aria-selected="locale === opt.value"
                  class="dropdown-option"
                  :class="{ active: locale === opt.value }"
                  @click.stop="chooseLanguage(opt.value)"
                >
                  <span>{{ opt.label }}</span>
                  <span v-if="locale === opt.value" class="dropdown-check" aria-hidden="true">✓</span>
                </button>
              </div>
            </Transition>
          </div>
        </div>
        <div class="pref-row">
          <span class="pref-label">{{ t('settings.theme') }}</span>
          <div ref="themeDropdownRef" class="dropdown-wrap">
            <button type="button" class="dropdown-trigger" :class="{ open: themeOpen }" @click.stop="themeOpen = !themeOpen">
              <span class="dropdown-value">{{ currentThemeLabel }}</span>
              <span class="dropdown-chevron" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>
              </span>
            </button>
            <Transition name="dropdown">
              <div v-show="themeOpen" class="dropdown-card" role="listbox">
                <button
                  v-for="opt in themeOptions"
                  :key="opt.value"
                  type="button"
                  role="option"
                  :aria-selected="theme === opt.value"
                  class="dropdown-option"
                  :class="{ active: theme === opt.value }"
                  @click.stop="chooseTheme(opt.value)"
                >
                  <span>{{ opt.label }}</span>
                  <span v-if="theme === opt.value" class="dropdown-check" aria-hidden="true">✓</span>
                </button>
              </div>
            </Transition>
          </div>
        </div>
        <div class="pref-row pref-row-toggle">
          <span class="pref-label">{{ t('settings.syncJoytrunkChat') }}</span>
          <button
            type="button"
            class="toggle-btn"
            :class="{ on: syncJoytrunkChat }"
            role="switch"
            :aria-checked="syncJoytrunkChat"
            @click="syncJoytrunkChat = !syncJoytrunkChat"
          >
            <span class="toggle-thumb"></span>
          </button>
        </div>
      </div>
    </section>

    <!-- 保存 -->
    <div class="actions">
      <button type="button" class="btn-save" :disabled="saving" @click="saveProfile">
        <span v-if="saving" class="btn-loading"></span>
        <span v-else>{{ saving ? t('common.loading') : t('settings.save') }}</span>
      </button>
      <p v-if="saveError" class="msg msg-error">{{ saveError }}</p>
      <p v-if="saveSuccess" class="msg msg-success">{{ t('settings.saved') }}</p>
    </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTheme } from '../composables/useTheme'
import { setLocale } from '../i18n'
import { api } from '../api'
import MobileTitleBar from '../components/MobileTitleBar.vue'

const { t, locale } = useI18n()
const { theme, setTheme } = useTheme()
const refreshTeam = inject('refreshTeam', null)
const isMobile = inject('isMobile', null)
const me = ref(null)
const nickname = ref('')
const avatarUrl = ref('')
const syncJoytrunkChat = ref(true)
const avatarError = ref(false)
const saving = ref(false)
const saveError = ref('')
const saveSuccess = ref(false)
const languageOpen = ref(false)
const themeOpen = ref(false)
const langDropdownRef = ref(null)
const themeDropdownRef = ref(null)

const languageOptions = [
  { value: 'zh', label: '简体中文' },
  { value: 'en', label: 'English' },
]
const themeOptions = computed(() => [
  { value: 'light', label: t('settings.themeLight') },
  { value: 'dark', label: t('settings.themeDark') },
])
const currentLanguageLabel = computed(() => languageOptions.find(o => o.value === locale.value)?.label ?? locale.value)
const currentThemeLabel = computed(() => themeOptions.value.find(o => o.value === theme.value)?.label ?? theme.value)

const avatarInitial = computed(() => {
  const name = nickname.value || me.value?.name || ''
  return name ? String(name).trim().charAt(0).toUpperCase() || '?' : '?'
})

const displayAvatarUrl = computed(() => {
  if (avatarError.value) return null
  const url = (avatarUrl.value || '').trim() || me.value?.avatar_url || null
  return url || null
})

async function loadMe() {
  try {
    me.value = await api.users.me()
    nickname.value = me.value?.name ?? ''
    avatarUrl.value = me.value?.avatar_url ?? ''
    syncJoytrunkChat.value = me.value?.sync_joytrunk_chat !== false
    avatarError.value = false
  } catch {
    me.value = null
  }
}

async function saveProfile() {
  saveError.value = ''
  saveSuccess.value = false
  saving.value = true
  try {
    await api.users.updateMe({
      name: nickname.value.trim() || undefined,
      avatar_url: avatarUrl.value.trim() || null,
      sync_joytrunk_chat: syncJoytrunkChat.value,
    })
    saveSuccess.value = true
    setTimeout(() => { saveSuccess.value = false }, 2000)
    await loadMe()
    if (refreshTeam) refreshTeam()
  } catch (e) {
    saveError.value = e.message || t('settings.saveFailed')
  } finally {
    saving.value = false
  }
}

function chooseLanguage(value) {
  setLocale(value)
  languageOpen.value = false
}

function chooseTheme(value) {
  setTheme(value)
  themeOpen.value = false
}

function handleClickOutside(e) {
  if (langDropdownRef.value && !langDropdownRef.value.contains(e.target)) languageOpen.value = false
  if (themeDropdownRef.value && !themeDropdownRef.value.contains(e.target)) themeOpen.value = false
}

onMounted(() => {
  loadMe()
  document.addEventListener('click', handleClickOutside)
})
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.page {
  max-width: 520px;
  margin: 0 auto;
  padding-bottom: 2rem;
}
.page-mobile {
  max-width: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  min-height: 100%;
  overflow: auto;
}
.page-mobile .mobile-content {
  flex: 1;
  padding: 1rem;
  padding-bottom: 2rem;
}
.page-title {
  margin: 0 0 1.75rem;
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--jt-text);
}

/* ---------- 上方：头像 + 昵称 ---------- */
.profile-section {
  display: flex;
  gap: 1.75rem;
  align-items: flex-start;
  padding: 1.75rem 1.5rem;
  margin-bottom: 1.5rem;
  background: var(--jt-card-bg);
  border: 1px solid var(--jt-border);
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.profile-avatar-wrap {
  flex-shrink: 0;
}

.profile-avatar {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--jt-primary) 0%, color-mix(in srgb, var(--jt-primary) 70%, #555) 100%);
  color: #fff;
  font-size: 2.25rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  box-shadow: 0 4px 16px color-mix(in srgb, var(--jt-primary) 25%, transparent);
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-initial {
  line-height: 1;
  letter-spacing: -0.02em;
}

.profile-fields {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.field-label {
  font-size: 0.8125rem;
  font-weight: 500;
  color: var(--jt-text-muted, #666);
  margin: 0;
}

.field-input {
  width: 100%;
  padding: 0.65rem 0.9rem;
  border: 1px solid var(--jt-border);
  border-radius: 10px;
  font-size: 0.9375rem;
  background: var(--jt-bg);
  color: var(--jt-text);
  transition: border-color 0.15s, box-shadow 0.15s;
}

.field-input::placeholder {
  color: var(--jt-text-muted, #999);
}

.field-input:focus {
  outline: none;
  border-color: var(--jt-primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--jt-primary) 18%, transparent);
}

/* ---------- 语言与主题 ---------- */
.prefs-section {
  margin-bottom: 1.5rem;
}

.section-title {
  margin: 0 0 0.75rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--jt-text-muted, #666);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.prefs-card {
  background: var(--jt-card-bg);
  border: 1px solid var(--jt-border);
  border-radius: 14px;
  overflow: visible;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
}

.pref-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  gap: 1rem;
  border-bottom: 1px solid var(--jt-border);
}

.pref-row:last-child {
  border-bottom: none;
}

.pref-row-toggle {
  flex-wrap: wrap;
}

.toggle-btn {
  width: 44px;
  height: 24px;
  border-radius: 12px;
  border: 1px solid var(--jt-border);
  background: var(--jt-text-muted, #94a3b8);
  cursor: pointer;
  padding: 0;
  position: relative;
  transition: background 0.2s ease, border-color 0.2s ease;
}

.toggle-btn.on {
  background: var(--jt-primary);
  border-color: var(--jt-primary);
}

.toggle-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  transition: transform 0.2s ease;
}

.toggle-btn.on .toggle-thumb {
  transform: translateX(20px);
}

.pref-label {
  font-size: 0.9375rem;
  font-weight: 500;
  color: var(--jt-text);
}

/* ---------- 卡片式下拉 ---------- */
.dropdown-wrap {
  position: relative;
}

.dropdown-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  min-width: 160px;
  padding: 0.6rem 1rem 0.6rem 1rem;
  border: 1px solid var(--jt-border);
  border-radius: 12px;
  font-size: 0.9375rem;
  font-weight: 500;
  background: var(--jt-card-bg);
  color: var(--jt-text);
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.dropdown-trigger:hover {
  border-color: var(--jt-text-muted, #94a3b8);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.dropdown-trigger.open {
  border-color: var(--jt-primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--jt-primary) 18%, transparent);
}

.dropdown-value {
  flex: 1;
  text-align: left;
}

.dropdown-chevron {
  display: flex;
  color: var(--jt-text-muted, #64748b);
  transition: transform 0.2s ease;
}

.dropdown-trigger.open .dropdown-chevron {
  transform: rotate(180deg);
}

.dropdown-chevron svg {
  width: 16px;
  height: 16px;
}

.dropdown-card {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  min-width: 100%;
  background: var(--jt-card-bg);
  border: 1px solid var(--jt-border);
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12);
  padding: 0.5rem;
  z-index: 50;
}

.dropdown-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 0.6rem 0.85rem;
  border: none;
  border-radius: 8px;
  font-size: 0.9375rem;
  font-weight: 500;
  background: transparent;
  color: var(--jt-text);
  cursor: pointer;
  text-align: left;
  transition: background 0.12s ease;
}

.dropdown-option:hover {
  background: color-mix(in srgb, var(--jt-primary) 12%, transparent);
}

.dropdown-option.active {
  background: color-mix(in srgb, var(--jt-primary) 18%, transparent);
  color: var(--jt-primary);
}

.dropdown-check {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--jt-primary);
}

/* 下拉出现/消失动画 */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ---------- 保存 ---------- */
.actions {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.75rem;
}

.btn-save {
  position: relative;
  padding: 0.7rem 1.5rem;
  border-radius: 10px;
  font-size: 0.9375rem;
  font-weight: 500;
  background: var(--jt-primary);
  color: #fff;
  border: none;
  cursor: pointer;
  transition: opacity 0.15s, transform 0.1s;
}

.btn-save:hover:not(:disabled) {
  opacity: 0.92;
  transform: translateY(-1px);
}

.btn-save:active:not(:disabled) {
  transform: translateY(0);
}

.btn-save:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.btn-loading {
  display: inline-block;
  width: 1em;
  height: 1em;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.msg {
  font-size: 0.875rem;
  margin: 0;
}

.msg-error {
  color: #dc2626;
}

.msg-success {
  color: var(--jt-primary);
  font-weight: 500;
}

@media (max-width: 480px) {
  .profile-section {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .profile-fields {
    width: 100%;
  }
}
</style>
