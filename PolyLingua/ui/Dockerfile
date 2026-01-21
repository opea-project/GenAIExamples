# Copyright (C) 2024
# SPDX-License-Identifier: Apache-2.0

FROM node:20-alpine AS base

# Install dependencies
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

# Build the application
FROM base AS builder
WORKDIR /app

# Accept build argument
ARG BACKEND_SERVICE_ENDPOINT
ENV BACKEND_SERVICE_ENDPOINT=$BACKEND_SERVICE_ENDPOINT

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Ensure public directory exists
RUN mkdir -p public

# Set environment for build
ENV NEXT_TELEMETRY_DISABLED 1

RUN npm run build

# Production image
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy build output
COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/package.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/public ./public

RUN chown -R nextjs:nodejs /app

USER nextjs

EXPOSE 5173

ENV PORT 5173
ENV HOSTNAME "0.0.0.0"

CMD ["npm", "start"]
