FROM node:22-alpine AS builder
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@latest --activate

COPY pnpm-lock.yaml pnpm-workspace.yaml package.json .npmrc ./
COPY packages/ ./packages/
COPY apps/web/ ./apps/web/
COPY apps/tracker/ ./apps/tracker/
RUN pnpm install --no-frozen-lockfile --ignore-scripts
RUN pnpm rebuild esbuild vue-demi
RUN pnpm --filter @en/tracker build
RUN pnpm --filter @en/web build

FROM nginx:alpine
COPY --from=builder /app/apps/web/dist /usr/share/nginx/html
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]