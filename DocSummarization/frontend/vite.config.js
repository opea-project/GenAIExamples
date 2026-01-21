import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5174,
    proxy: {
      '/v1': {
        target: process.env.BACKEND_SERVICE_ENDPOINT || 'http://localhost:8888',
        changeOrigin: true
      }
    }
  }
})
