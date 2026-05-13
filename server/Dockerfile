FROM node:22-alpine AS builder
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@latest --activate

COPY pnpm-lock.yaml pnpm-workspace.yaml package.json .npmrc ./
COPY packages/ ./packages/
COPY server/package.json server/nest-cli.json server/tsconfig*.json server/prisma.config.ts ./server/
COPY server/apps/server/tsconfig*.json ./server/apps/server/
COPY server/apps/ai/tsconfig*.json ./server/apps/ai/
COPY server/libs/shared/tsconfig*.json ./server/libs/shared/
COPY apps/tracker/package.json ./apps/tracker/
COPY apps/web/package.json ./apps/web/
RUN pnpm install --no-frozen-lockfile --ignore-scripts
RUN pnpm rebuild esbuild vue-demi

COPY . .
ENV DATABASE_URL="postgresql://u:p@localhost:5432/db"
RUN cd server && npx prisma generate && cd ..
RUN pnpm --filter @en/tracker build
RUN pnpm --filter @en/server build

FROM node:22-alpine AS runner
WORKDIR /app
RUN corepack enable && corepack prepare pnpm@latest --activate

COPY --from=builder /app/server/dist ./server/dist
COPY --from=builder /app/server/node_modules ./server/node_modules
COPY --from=builder /app/server/prisma ./server/prisma
COPY --from=builder /app/server/package.json ./server/
COPY --from=builder /app/packages ./packages
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json /app/pnpm-workspace.yaml /app/

EXPOSE 3000 3001
CMD ["node", "server/dist/apps/server/main.js"]