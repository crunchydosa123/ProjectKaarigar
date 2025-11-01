# Step 1: Build the React app
FROM node:20 AS build

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Step 2: Serve the build using a lightweight web server
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html

# Optional: Add custom nginx config for SPA routing (important for React Router)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
