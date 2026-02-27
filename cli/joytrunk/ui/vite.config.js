import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  build: {
    outDir: path.resolve(__dirname, '../gateway/static'),
    emptyOutDir: true,
  },
  base: '/',
  server: {
    port: 32893,
    proxy: {
      '/api': {
        target: 'http://localhost:32890',
        changeOrigin: true,
      },
    },
  },
})
