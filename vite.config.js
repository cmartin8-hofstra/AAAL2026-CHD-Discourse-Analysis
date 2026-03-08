import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/AAAL2026-CHD-Discourse-Analysis/',
  build: {
    outDir: 'docs',
    emptyOutDir: true,
  },
})
