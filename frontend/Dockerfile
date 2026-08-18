# syntax=docker/dockerfile:1.9
# ---------------------------------------------------------------------------
# Clos Peyredoule web. Vite compiles the site, nginx serves the static build.
#
# VITE_API_BASE_URL is baked in at build time, as Vite inlines it. It must be
# same-site with the address the site is served from, or the browser will drop
# the SameSite=Lax session cookie and the guest guide will never unlock.
# ---------------------------------------------------------------------------
FROM node:26-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build


FROM nginx:1.29-alpine AS runtime

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --spider http://127.0.0.1/ || exit 1
