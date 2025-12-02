FROM node:22-bookworm-slim AS pruner

WORKDIR /repo

RUN corepack enable && corepack prepare pnpm@9.0.0 --activate

ARG APP_DIR=apps/web
ENV APP_DIR=${APP_DIR}

COPY . .

RUN PKG_NAME="$(node -p "require('./${APP_DIR}/package.json').name")"\
    && pnpm dlx turbo prune --scope="$PKG_NAME" --docker

FROM node:22-bookworm-slim AS builder

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@9.0.0 --activate

COPY --from=pruner /repo/out/json/ ./

RUN pnpm install --frozen-lockfile

COPY --from=pruner /repo/out/full/ ./

ENV NEXT_TELEMETRY_DISABLED=1
ARG APP_DIR=apps/web
RUN pnpm --filter "./${APP_DIR}" build

FROM node:22-bookworm-slim AS runner

WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0

ARG APP_DIR=apps/web

COPY --from=builder /app/${APP_DIR}/.next/standalone ./
COPY --from=builder /app/${APP_DIR}/public ./public
COPY --from=builder /app/${APP_DIR}/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
