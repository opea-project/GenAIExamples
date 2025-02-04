// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import os from "os";

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
    port: 3000,
  },
  test: {
    globals: true,
    environment: "jsdom",
  },
  define: {
    // Dynamically set the hostname for the VITE_TEXT_TO_SQL_URL
    "import.meta.env.VITE_TEXT_TO_SQL_URL": JSON.stringify(`http://${process.env.TEXT_TO_SQL_URL}`),
    "import.meta.env": process.env,
  },
});
