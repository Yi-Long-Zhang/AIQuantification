import { defineConfig, presetUno, presetAttributify, presetIcons } from 'unocss'

export default defineConfig({
  presets: [
    presetUno(),
    presetAttributify(),
    presetIcons()
  ],
  theme: {
    colors: {
      primary: '#58a6ff',
      background: '#0d1117',
      surface: '#161b22',
      border: '#30363d'
    }
  }
})
