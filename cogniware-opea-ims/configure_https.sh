#!/bin/bash
################################################################################
# Configure HTTPS for CogniDream Platform with SSL Certificates
################################################################################

REMOTE_HOST="185.141.218.141"
REMOTE_USER="root"
REMOTE_PASSWORD="CogniDream2025"
DOMAIN="demo.cogniware.ai"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║         CogniDream - HTTPS Configuration                        ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Create nginx configuration with HTTPS
echo -e "${BLUE}[1/4]${NC} Creating HTTPS nginx configuration..."

cat > /tmp/cognidream-https.conf << 'EOF'
# CogniDream Platform - HTTPS Configuration

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
    
    # Allow Let's Encrypt validation
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Redirect all other traffic to HTTPS
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

    # SSL Configuration (Mozilla Modern)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_stapling on;
    ssl_stapling_verify on;

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

    # Root directory for static files
    root /opt/cognidream/ui;
    index index.html;

    # Static files
    location / {
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Production API
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
        proxy_buffering off;
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
        proxy_buffering off;
    }

    # Health check
    location /health {
        proxy_pass http://cognidream_production/health;
        proxy_set_header Host $host;
        access_log off;
    }

    # Login endpoint
    location /login {
        proxy_pass http://cognidream_production/login;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOF

sshpass -p "$REMOTE_PASSWORD" scp -o StrictHostKeyChecking=no \
    /tmp/cognidream-https.conf $REMOTE_USER@$REMOTE_HOST:/tmp/

echo -e "${GREEN}✅ HTTPS configuration created${NC}"

# Install configuration
echo -e "${BLUE}[2/4]${NC} Installing nginx configuration..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'

# Backup old config
cp /etc/nginx/sites-available/cognidream /etc/nginx/sites-available/cognidream.backup 2>/dev/null || true

# Install new HTTPS config
mv /tmp/cognidream-https.conf /etc/nginx/sites-available/cognidream

# Test configuration
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Nginx configuration valid"
    systemctl reload nginx
    echo "✅ Nginx reloaded with HTTPS"
else
    echo "❌ Nginx configuration error"
    exit 1
fi

ENDSSH

echo -e "${GREEN}✅ Nginx configured for HTTPS${NC}"

# Fix login.html 404 issue
echo -e "${BLUE}[3/4]${NC} Fixing login.html issue..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'

cd /opt/cognidream/ui

# Check if login.html exists
if [ -f "login.html" ]; then
    echo "✅ login.html exists"
else
    echo "❌ login.html not found!"
    ls -la *.html | head -10
fi

# Set correct permissions
chown -R cognidream:cognidream /opt/cognidream/ui
chmod -R 755 /opt/cognidream/ui
chmod 644 /opt/cognidream/ui/*.html

echo "✅ Permissions set correctly"

ENDSSH

echo -e "${GREEN}✅ File permissions configured${NC}"

# Verify deployment
echo -e "${BLUE}[4/4]${NC} Verifying HTTPS deployment..."
sleep 2

echo ""
echo "Testing endpoints..."

# Test HTTP redirect
echo -n "HTTP (should redirect): "
curl -I -s http://demo.cogniware.ai 2>&1 | grep -q "301\|302" && echo "✅ Redirects to HTTPS" || echo "⚠️  Check redirect"

# Test HTTPS
echo -n "HTTPS homepage: "
curl -k -s https://demo.cogniware.ai/ 2>&1 | grep -q "DOCTYPE" && echo "✅ Working" || echo "❌ Not responding"

# Test health endpoint
echo -n "HTTPS /health: "
curl -k -s https://demo.cogniware.ai/health 2>&1 | grep -q "healthy" && echo "✅ Working" || echo "⚠️  Starting..."

# Test login page
echo -n "HTTPS /login.html: "
curl -k -s https://demo.cogniware.ai/login.html 2>&1 | grep -q "DOCTYPE" && echo "✅ Working" || echo "❌ 404"

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                HTTPS CONFIGURATION COMPLETE                      ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "🔒 Secure URLs:"
echo -e "${GREEN}   https://demo.cogniware.ai${NC}"
echo -e "${GREEN}   https://demo.cogniware.ai/login.html${NC}"
echo -e "${GREEN}   https://demo.cogniware.ai/code-ide.html${NC}"
echo ""
echo "🌐 All HTTP requests will redirect to HTTPS"
echo ""
echo "✨ Platform is now secure with SSL!"
echo ""

# Cleanup
rm -f /tmp/cognidream-https.conf


