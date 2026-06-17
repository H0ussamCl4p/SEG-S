# ==========================================
# Frontend Dockerfile (Speed Optimized)
# Target: <5s incremental, <40s clean build
# ==========================================

FROM node:20-alpine AS base
WORKDIR /app
RUN apk add --no-cache libc6-compat

# Dependencies stage with aggressive caching
FROM base AS deps

# Copy lock file first (changes least)
COPY package-lock.json* ./
COPY package.json ./

# Use BuildKit cache mount - reuses downloaded packages
RUN --mount=type=cache,target=/root/.npm \
    npm ci --prefer-offline --no-audit

# Build stage
FROM base AS builder

# Copy deps from previous stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source (changes most frequently - last)
COPY . .

# NEXT_PUBLIC_* must be set at build time — Next.js bakes them into the client
# bundle. Runtime env vars cannot override these once the image is built.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_AUTH_URL=http://localhost:8001
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_AUTH_URL=$NEXT_PUBLIC_AUTH_URL
ENV NEXT_TELEMETRY_DISABLED=1 NODE_ENV=production

# Build with standalone output (faster startup)
RUN npm run build

# Minimal runtime
FROM base AS runner

ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy only what's needed for production
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
