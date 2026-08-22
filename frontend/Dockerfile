# syntax=docker/dockerfile:1

# Buyam-Sellam frontend — Next.js + Tailwind.
# Build context: repository root (so the backend is not needed at build time,
# but the whole repo is the context — see the root .dockerignore).

# --- Build stage -----------------------------------------------------------
FROM node:20-alpine AS builder
WORKDIR /app

# Install dependencies first (layer caching).
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# The browser talks to the backend through the published port. Override with a
# build arg if you host the API elsewhere.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

COPY frontend/ ./
RUN npm run build

# --- Run stage -------------------------------------------------------------
FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/package.json /app/package-lock.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/next.config.mjs ./next.config.mjs
# Static assets (logo, backgrounds, etc.) — served from public/ at runtime.
COPY --from=builder /app/public ./public

EXPOSE 3000
CMD ["npm", "run", "start"]
