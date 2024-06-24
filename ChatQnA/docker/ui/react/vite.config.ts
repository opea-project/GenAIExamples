// Copyright (C) 2024 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

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
  test: {
    globals: true,
    environment: "jsdom",
  },
  define: {
    "import.meta.env": process.env,
  },
});
