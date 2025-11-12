// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_BACKEND_URL: process.env.BACKEND_SERVICE_ENDPOINT || "http://localhost:8888",
  },
};

module.exports = nextConfig;
