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
ARG REACT_APP_API_URL=

# Build application
RUN REACT_APP_API_URL=${REACT_APP_API_URL} npm run build

# Production image
FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1
