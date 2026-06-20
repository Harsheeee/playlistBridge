# Multi-stage build for Vite + React + TypeScript frontend
FROM node:18-alpine AS build

WORKDIR /app

# Install dependencies (copy package files first for caching)
COPY package*.json ./
RUN npm ci --silent || npm install --silent

# Copy the rest and build
COPY . .
RUN npm run build

# Serve the app using serve or nginx. Let's use a simple node server or nginx.
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
