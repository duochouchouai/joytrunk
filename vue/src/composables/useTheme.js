import { ref, onMounted, watch } from 'vue'

const STORAGE_KEY = 'joytrunk_theme'
const THEMES = ['light', 'dark']

function getStored() {
  if (typeof localStorage === 'undefined') return 'light'
  const s = localStorage.getItem(STORAGE_KEY)
  return THEMES.includes(s) ? s : 'light'
}

function applyTheme(theme) {
  if (typeof document === 'undefined') return
  document.documentElement.setAttribute('data-theme', theme)
}

// Single source of truth so all components share the same theme
const theme = ref(getStored())

// Apply immediately so no flash
applyTheme(theme.value)

export function useTheme() {
  onMounted(() => {
    applyTheme(theme.value)
  })

  watch(theme, (val) => {
    applyTheme(val)
    if (typeof localStorage !== 'undefined') localStorage.setItem(STORAGE_KEY, val)
  })

  function setTheme(val) {
    if (THEMES.includes(val)) theme.value = val
  }

  return { theme, setTheme, themes: THEMES }
}
