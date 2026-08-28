import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig(({ command }) => {
  return {
    plugins: [
      tailwindcss(),
      react()
    ],
    // Only apply the subpath base in production build
    base: command === 'build' ? '/pilates/app/' : '/',
  }
})
