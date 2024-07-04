import { defineConfig } from "vite";
import react from "@vitejs/plugin-react"

// https://vitejs.dev/config/
export default defineConfig({
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@import "./src/styles/styles.scss";`,
      },
    },
  },
  plugins: [react()],
  server: {
    port: 80,
  },
  define: {
    "import.meta.env": process.env,
  },
});
