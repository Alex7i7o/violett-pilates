import path from 'path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

import fs from 'fs'

const resolvePkg = (pkg: string) => {
  const localPath = path.resolve(__dirname, 'node_modules', pkg);
  if (fs.existsSync(localPath)) return localPath;
  const parentPath = path.resolve(__dirname, '../node_modules', pkg);
  if (fs.existsSync(parentPath)) return parentPath;
  return localPath;
};

// Selects the correct plugin loader based on which client is being built.
// VITE_CLIENT_ID is injected as a Docker build arg in docker-compose.yml.
// For local dev, defaults to 'pilates'.
const clientId = process.env.VITE_CLIENT_ID || 'pilates';
const pluginLoaderPath = path.resolve(__dirname, `./src/core/pluginLoader.${clientId}.tsx`);

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    tailwindcss(),
    react()
  ],
  base: process.env.VITE_BASE_URL || '/',
  define: {
    // Make the client ID available at runtime for any component that needs it
    'import.meta.env.VITE_CLIENT_ID': JSON.stringify(clientId),
  },
  resolve: {
    alias: {
      // This is the key alias: redirects all imports of 'pluginLoader' to the
      // client-specific file, so Vite only bundles the plugins for that client.
      '@/core/pluginLoader': pluginLoaderPath,
      '@': path.resolve(__dirname, './src'),
      '@plugins': path.resolve(__dirname, '../plugins'),
      'react': resolvePkg('react'),
      'react-dom': resolvePkg('react-dom'),
      'framer-motion': resolvePkg('framer-motion'),
      'lucide-react': resolvePkg('lucide-react'),
      'react-router-dom': resolvePkg('react-router-dom'),
      'sonner': resolvePkg('sonner'),
      '@tanstack/react-query': resolvePkg('@tanstack/react-query'),
      'axios': resolvePkg('axios'),
      'recharts': resolvePkg('recharts')
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
