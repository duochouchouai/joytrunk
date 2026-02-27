import { createI18n } from 'vue-i18n'
import zh from './locales/zh'
import en from './locales/en'

const STORAGE_KEY = 'joytrunk_locale'
const defaultLocale = () => {
  if (typeof localStorage === 'undefined') return 'zh'
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved === 'en' || saved === 'zh') return saved
  return 'zh'
}

export const i18n = createI18n({
  legacy: false,
  locale: defaultLocale(),
  fallbackLocale: 'zh',
  messages: { zh, en },
})

export function setLocale(locale) {
  if (locale === 'zh' || locale === 'en') {
    i18n.global.locale.value = locale
    if (typeof localStorage !== 'undefined') localStorage.setItem(STORAGE_KEY, locale)
  }
}

export function getLocale() {
  return i18n.global.locale.value
}
