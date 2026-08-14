# Multi-stage or lightweight Node alpine base
FROM node:22-alpine

WORKDIR /app

# Copy server package files and install production dependencies
COPY server/package*.json ./server/
WORKDIR /app/server
RUN npm ci --only=production

# Copy rest of the application
WORKDIR /app
COPY server ./server
COPY public ./public

EXPOSE 3000

ENV PORT=3000
ENV NODE_ENV=production

WORKDIR /app/server
CMD ["node", "--experimental-sqlite", "server.js"]
