# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# Multi-stage build for Next.js production optimization
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Install dependencies (including dev dependencies for build)
# Copy package files - copy all package*.json files from frontend
# This handles both package.json and package-lock.json if it exists
COPY frontend/package*.json ./
# Use npm ci if lock file exists, otherwise use npm install
RUN if [ -f package-lock.json ]; then \
      echo "Found package-lock.json, using npm ci for deterministic build"; \
      npm ci --legacy-peer-deps || (echo "npm ci failed, falling back to npm install" && npm install --legacy-peer-deps); \
    else \
      echo "package-lock.json not found, using npm install"; \
      npm install --legacy-peer-deps; \
    fi

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ .

# Set environment variables
ENV NEXT_TELEMETRY_DISABLED 1
ENV NODE_ENV production

# Build Next.js
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy necessary files
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

CMD ["node", "server.js"]

