# Build stage
FROM node:22-alpine AS builder
WORKDIR /app
RUN corepack enable && corepack prepare yarn@stable --activate
COPY package*.json ./
COPY . .
RUN yarn

# Environment variables
ARG NEXT_PUBLIC_BACKEND_URL=https://api.insights.globalct.com
ARG NEXT_PUBLIC_APP_VERSION=1.0.0

RUN yarn build

# Production stage
FROM node:22-alpine AS runner
WORKDIR /app

ENV PORT=3000
ENV NODE_ENV=production

# Install production dependencies
RUN corepack enable && corepack prepare yarn@stable --activate
COPY package*.json ./
RUN yarn

# Copy standalone build and static files
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["node", "server.js"]