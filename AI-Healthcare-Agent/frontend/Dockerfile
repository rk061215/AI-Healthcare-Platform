# ──────────────────────────────────────────────
# Frontend Dockerfile
# ──────────────────────────────────────────────

# ---- Dev Stage ----
FROM node:20.18-alpine AS dev

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]


# ---- Build Stage ----
FROM node:20.18-alpine AS builder

WORKDIR /app

ENV NEXT_TELEMETRY_DISABLED=1

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

RUN npm run build


# ---- Production Stage ----
FROM node:20.18-alpine AS production

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system app && adduser --system --group app

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

USER app

EXPOSE 3000

CMD ["node", "server.js"]
