FROM node:22-alpine AS base

WORKDIR /app

# Dependencies
COPY package.json package-lock.json* ./
RUN npm ci

# Build
COPY . .
# NEXT_PUBLIC_* vars are inlined at build time — must be passed as a build arg.
# Render injects env vars as Docker build args automatically.
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
RUN npm run build

# Production
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
# Bind to all interfaces so Render's proxy can reach the server
ENV HOSTNAME=0.0.0.0

COPY --from=base /app/.next/standalone ./
COPY --from=base /app/.next/static ./.next/static
COPY --from=base /app/public ./public

EXPOSE 3000
# Render injects $PORT; Next.js standalone server reads PORT env var automatically
CMD ["node", "server.js"]

