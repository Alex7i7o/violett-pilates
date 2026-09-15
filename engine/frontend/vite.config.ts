import path from 'path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    tailwindcss(),
    react()
  ],
  base: process.env.VITE_BASE_URL || '/',
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@plugins': path.resolve(__dirname, '../plugins'),
      'react': path.resolve(__dirname, 'node_modules/react'),
      'react-dom': path.resolve(__dirname, 'node_modules/react-dom'),
      'framer-motion': path.resolve(__dirname, 'node_modules/framer-motion'),
      'lucide-react': path.resolve(__dirname, 'node_modules/lucide-react'),
      'react-router-dom': path.resolve(__dirname, 'node_modules/react-router-dom'),
      'sonner': path.resolve(__dirname, 'node_modules/sonner'),
      '@tanstack/react-query': path.resolve(__dirname, 'node_modules/@tanstack/react-query'),
      'axios': path.resolve(__dirname, 'node_modules/axios')
    }
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts'
  },
  preview: {
    host: true,
    allowedHosts: true,
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    }
  },
  server: {
    host: true,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/admin': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      }
    },
    fs: {
      allow: ['..']
    }
  }
})
