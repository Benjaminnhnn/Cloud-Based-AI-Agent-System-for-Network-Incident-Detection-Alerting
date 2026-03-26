FROM node:18-alpine as base

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source
COPY . .

# Development image (hot reload)
FROM base as dev
EXPOSE 3000
CMD ["npm", "start"]

# Build production assets
FROM base as build

# Accept build args
ARG REACT_APP_API_URL=http://localhost:8000

# Build application
RUN REACT_APP_API_URL=${REACT_APP_API_URL} npm run build

# Production image
FROM node:18-alpine

WORKDIR /app

# Install serve to run the React app
RUN npm install -g serve

# Copy built app from build stage
COPY --from=build /app/build ./build

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Run application
CMD ["serve", "-s", "build", "-l", "3000"]
