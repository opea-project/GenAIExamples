# Build stage
FROM node:18-alpine AS build

WORKDIR /app

# Copy package.json
COPY package.json ./
RUN npm install

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html

# Create nginx config with increased file upload limit and no-cache headers
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    client_max_body_size 500M; \
    \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
        \
        # Disable cache for HTML \
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"; \
        add_header Pragma "no-cache"; \
        add_header Expires "0"; \
    } \
    \
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ { \
        root /usr/share/nginx/html; \
        expires -1; \
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0"; \
    } \
    \
    location /v1/ { \
        proxy_pass http://backend:8000; \
        proxy_http_version 1.1; \
        proxy_set_header Upgrade $http_upgrade; \
        proxy_set_header Connection "upgrade"; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header X-Forwarded-Proto $scheme; \
        client_max_body_size 500M; \
        proxy_read_timeout 600s; \
        proxy_connect_timeout 600s; \
        proxy_send_timeout 600s; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
