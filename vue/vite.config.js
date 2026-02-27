import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  optimizeDeps: {
    include: ['vue', 'vue-router', 'vue-i18n'],
  },
  server: {
    port: 32892,
    proxy: {
      '/api': { target: 'http://localhost:32891', changeOrigin: true },
    },
  },
  test: {
    environment: 'node',
    globals: true,
  },
})
