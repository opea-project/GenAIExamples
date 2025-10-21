#!/bin/bash
################################################################################
# Fix nginx configuration to properly serve static files
################################################################################

REMOTE_HOST="185.141.218.141"
REMOTE_USER="root"
REMOTE_PASSWORD="CogniDream2025"

echo "Fixing nginx configuration..."

# Create corrected nginx configuration
cat > /tmp/cognidream-fixed.conf << 'EOF'
# CogniDream Platform - Fixed HTTPS Configuration

upstream cognidream_production {
    server 127.0.0.1:8090;
    keepalive 32;
}

upstream cognidream_mcp {
    server 127.0.0.1:8091;
    keepalive 32;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name demo.cogniware.ai 185.141.218.141;
    
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    location / {
        return 301 https://demo.cogniware.ai$request_uri;
    }
}

# HTTPS Server
server {
    listen 443 ssl http2;
    server_name demo.cogniware.ai;

    # SSL Certificates
    ssl_certificate /etc/letsencrypt/live/demo.cogniware.ai/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/demo.cogniware.ai/privkey.pem;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/cognidream-access.log;
    error_log /var/log/nginx/cognidream-error.log;

    # File upload size
    client_max_body_size 100M;

    # Root directory
    root /opt/cognidream/ui;
    index index.html;

    # API endpoints (must come before static files)
    location /api/ {
        proxy_pass http://cognidream_production;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 30s;
    }

    # MCP Server
    location /mcp/ {
        proxy_pass http://cognidream_mcp;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    # Health check endpoint
    location = /health {
        proxy_pass http://cognidream_production/health;
        proxy_set_header Host $host;
        access_log off;
    }

    # Login endpoint (API, not static file)
    location = /login {
        proxy_pass http://cognidream_production/login;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Content-Type "application/json";
    }

    # Static HTML files
    location ~* \.html$ {
        root /opt/cognidream/ui;
        try_files $uri =404;
        add_header Cache-Control "no-cache, must-revalidate";
    }

    # Static assets (JS, CSS, images)
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        root /opt/cognidream/ui;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Default location - serve static files or index.html
    location / {
        root /opt/cognidream/ui;
        try_files $uri $uri/ /index.html;
    }
}
EOF

sshpass -p "$REMOTE_PASSWORD" scp -o StrictHostKeyChecking=no \
    /tmp/cognidream-fixed.conf $REMOTE_USER@$REMOTE_HOST:/tmp/

sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'

# Install fixed configuration
mv /tmp/cognidream-fixed.conf /etc/nginx/sites-available/cognidream

# Test and reload
nginx -t && systemctl reload nginx

echo "✅ Nginx configuration updated and reloaded"

ENDSSH

echo ""
echo "Testing fixed configuration..."
sleep 2

echo "Testing login.html:"
curl -k -s https://demo.cogniware.ai/login.html | head -3

echo ""
echo "✅ Configuration fixed!"
echo ""
echo "🔒 Access platform: https://demo.cogniware.ai"
echo ""

rm -f /tmp/cognidream-fixed.conf

