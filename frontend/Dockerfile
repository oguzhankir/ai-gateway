# Multi-stage build for frontend
FROM node:20-slim as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM node:20-slim as runner

WORKDIR /app

ENV NODE_ENV=production

# Copy built application
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/next.config.js ./
# Create public directory (Next.js will work without it)
RUN mkdir -p ./public

# Install production dependencies only
RUN npm install --only=production

# Expose port
EXPOSE 3000

# Start application
CMD ["npm", "start"]

