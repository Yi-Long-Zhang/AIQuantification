/// <reference types="vitest" />
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import UnoCSS from 'unocss/vite'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    UnoCSS()
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/agent': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/market': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/strategies': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/backtest': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/alpha': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/health': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['src/**/*.{test,spec}.{ts,js}'],
    setupFiles: ['src/test-setup.ts'],
  }
})
