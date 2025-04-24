// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import react from "@vitejs/plugin-react";
import path from "path";

import { defineConfig } from "vite";
import { visualizer } from "rollup-plugin-visualizer";
import compression from "vite-plugin-compression";
import terser from "@rollup/plugin-terser";
import sassDts from "vite-plugin-sass-dts";
import svgr from "vite-plugin-svgr";

export default defineConfig({
  base: "/",
  optimizeDeps: {
    include: ["**/*.scss"], // Include all .scss files
  },
  modulePreload: {
    polyfill: true, // Ensures compatibility
  },
  css: {
    modules: {
      // Enable CSS Modules for all .scss files
      localsConvention: "camelCaseOnly",
    },
  },
  commonjsOptions: {
    esmExternals: true,
  },
  server: {
    // https: true,
    host: "0.0.0.0",
    port: 5173,
  },
  build: {
    sourcemap: false,
    rollupOptions: {
      // output: {
      //     manualChunks(id) {
      //         if (id.includes('node_modules')) {

      //             if (id.match(/react-dom|react-router|react-redux/)) {
      //                 return 'react-vendor';
      //             }

      //             // // Code render files
      //             // if (id.match(/react-syntax-highlighter|react-markdown|gfm|remark|refractor|micromark|highlight|mdast/)) {
      //             //     return 'code-vendor';
      //             // }

      //             if (id.match(/emotion|mui|styled-components/)) {
      //                 return 'style-vendor';
      //             }

      //             if (id.match(/keycloak-js|axios|notistack|reduxjs|fetch-event-source|azure/)) {
      //                 return 'utils-vendor';
      //             }

      //             const packages = id.toString().split('node_modules/')[1].split('/')[0];
      //             return `vendor-${packages}`;
      //         }
      //     }
      // },
      plugins: [
        terser({
          format: { comments: false },
          compress: {
            drop_console: true,
            drop_debugger: true,
          },
        }),
      ],
    },
    chunkSizeWarningLimit: 500,
    assetsInlineLimit: 0,
  },
  plugins: [
    svgr(),
    react(),
    // sassDts({
    //     enabledMode: []//['production'], // Generate type declarations on build
    // }),
    compression({
      algorithm: "gzip",
      ext: ".gz",
      deleteOriginFile: false,
      threshold: 10240,
    }),
    visualizer({
      filename: "./dist/stats.html", // Output stats file
      open: true, // Automatically open in the browser
      gzipSize: true, // Show gzipped sizes
      brotliSize: true, // Show Brotli sizes
    }),
  ],
  resolve: {
    alias: {
      "@mui/styled-engine": "@mui/styled-engine-sc",
      "@components": path.resolve(__dirname, "src/components/"),
      "@shared": path.resolve(__dirname, "src/shared/"),
      "@contexts": path.resolve(__dirname, "src/contexts/"),
      "@redux": path.resolve(__dirname, "src/redux/"),
      "@services": path.resolve(__dirname, "src/services/"),
      "@pages": path.resolve(__dirname, "src/pages/"),
      "@layouts": path.resolve(__dirname, "src/layouts/"),
      "@assets": path.resolve(__dirname, "src/assets/"),
      "@utils": path.resolve(__dirname, "src/utils/"),
      "@icons": path.resolve(__dirname, "src/icons/"),
      "@root": path.resolve(__dirname, "src/"),
    },
  },
  assetsInclude: ["**/*.svg"], // Ensure Vite processes .svg files
  // define: {
  //     "import.meta.env": process.env,
  //   },
});
