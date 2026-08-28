import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ command }) => {
  return {
    plugins: [react()],
    // Only apply the subpath base in production build
    base: command === 'build' ? '/pilates/app/' : '/',
  }
})
