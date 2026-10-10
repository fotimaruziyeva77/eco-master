# Mini App and admin panel, served by Caddy with automatic HTTPS (Telegram needs HTTPS).
# Build context: the repository root (see deploy/docker-compose.yml).

FROM node:22-alpine AS build
WORKDIR /src
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend ./
# Values from the build win over frontend/.env.production.
ARG VITE_BOT_USERNAME
ARG VITE_WEBAPP_SHORT_NAME=app
ENV VITE_BOT_USERNAME=$VITE_BOT_USERNAME \
    VITE_WEBAPP_SHORT_NAME=$VITE_WEBAPP_SHORT_NAME
# The build fails if the first-load JavaScript goes over the TZ 13 budget.
RUN npm run build && npm run size

FROM caddy:2-alpine
COPY deploy/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /src/dist /srv
