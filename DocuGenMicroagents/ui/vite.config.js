import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 3000,
    proxy: {
      '/api': {
        // Use 'backend' hostname in Docker, 'localhost' when running locally
        target: process.env.VITE_API_TARGET || 'http://localhost:5001',
        changeOrigin: true
      }
    }
  }
})
