import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      // Proxy API requests to Django backend
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      // Proxy specific Django endpoints (use regex to be more specific)
      '/login': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      // Patient chatbot endpoint only (to avoid proxying frontend routes)
      '/patient/chatbot/': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      // Use exact paths to avoid catching /src/*
      '/sr/': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/ar/': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/bc/': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/jj/': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/srtwo': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
      '/admin': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
