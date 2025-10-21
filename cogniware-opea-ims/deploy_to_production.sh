#!/bin/bash
################################################################################
# CogniDream Platform - Production Deployment Script
# Deploys to remote server with nginx configuration
################################################################################

# Remote server details
REMOTE_HOST="185.141.218.141"
REMOTE_USER="root"
REMOTE_PASSWORD="CogniDream2025"
DEPLOY_DIR="/opt/cognidream"
APP_USER="cognidream"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║          CogniDream Platform - Production Deployment            ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo -e "${RED}❌ sshpass is not installed${NC}"
    echo "Install with: sudo apt-get install sshpass"
    exit 1
fi

echo -e "${BLUE}[1/10]${NC} Checking connectivity to remote server..."
if sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST "echo 'Connection successful'" 2>/dev/null; then
    echo -e "${GREEN}✅ Connected to $REMOTE_HOST${NC}"
else
    echo -e "${RED}❌ Failed to connect to remote server${NC}"
    exit 1
fi

echo -e "${BLUE}[2/10]${NC} Creating deployment package..."
cd "$(dirname "$0")"
tar -czf /tmp/cognidream-deploy.tar.gz \
    --exclude='venv' \
    --exclude='build' \
    --exclude='build_simple' \
    --exclude='build_simple_engine' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='*.log' \
    --exclude='node_modules' \
    python/ ui/ scripts/ databases/ documents/ projects/ requirements.txt config.json

echo -e "${GREEN}✅ Package created${NC}"

echo -e "${BLUE}[3/10]${NC} Transferring files to remote server..."
sshpass -p "$REMOTE_PASSWORD" scp -o StrictHostKeyChecking=no \
    /tmp/cognidream-deploy.tar.gz \
    $REMOTE_USER@$REMOTE_HOST:/tmp/

echo -e "${GREEN}✅ Files transferred${NC}"

echo -e "${BLUE}[4/10]${NC} Setting up remote environment..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'

set -e

# Create application user
if ! id -u cognidream &>/dev/null; then
    useradd -r -s /bin/bash -m -d /home/cognidream cognidream
    echo "✅ Created application user: cognidream"
else
    echo "✅ Application user already exists"
fi

# Create deployment directory
mkdir -p /opt/cognidream
chown -R cognidream:cognidream /opt/cognidream

# Extract package
cd /opt/cognidream
tar -xzf /tmp/cognidream-deploy.tar.gz
chown -R cognidream:cognidream /opt/cognidream

echo "✅ Files extracted to /opt/cognidream"

# Create necessary directories
mkdir -p logs databases documents projects
chown -R cognidream:cognidream logs databases documents projects

ENDSSH

echo -e "${GREEN}✅ Remote environment configured${NC}"

echo -e "${BLUE}[5/10]${NC} Installing system dependencies..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'

# Update package lists
apt-get update -qq

# Install Python and dependencies
apt-get install -y -qq \
    python3.12 \
    python3.12-venv \
    python3-pip \
    nginx \
    supervisor \
    tesseract-ocr \
    git \
    curl

echo "✅ System dependencies installed"

ENDSSH

echo -e "${GREEN}✅ System dependencies installed${NC}"

echo -e "${BLUE}[6/10]${NC} Setting up Python virtual environment..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'

cd /opt/cognidream

# Create virtual environment
sudo -u cognidream python3.12 -m venv venv

# Install Python packages
sudo -u cognidream venv/bin/pip install --upgrade pip setuptools wheel --quiet
sudo -u cognidream venv/bin/pip install -r requirements.txt --quiet

echo "✅ Python packages installed"

ENDSSH

echo -e "${GREEN}✅ Python environment ready${NC}"

echo -e "${BLUE}[7/10]${NC} Configuring nginx..."

# Create nginx configuration
cat > /tmp/cognidream-nginx.conf << 'EOF'
# CogniDream Platform - Nginx Configuration

upstream cognidream_production {
    server localhost:8090;
}

upstream cognidream_mcp {
    server localhost:8091;
}

upstream cognidream_admin {
    server localhost:8099;
}

server {
    listen 80;
    server_name 185.141.218.141;

    # Increase body size for file uploads
    client_max_body_size 100M;

    # Logging
    access_log /var/log/nginx/cognidream-access.log;
    error_log /var/log/nginx/cognidream-error.log;

    # Static files (UI)
    location / {
        root /opt/cognidream/ui;
        index index.html;
        try_files $uri $uri/ =404;
        
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
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
    }

    # MCP Server
    location /mcp/ {
        proxy_pass http://cognidream_mcp;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
    }

    # Admin API
    location /admin/ {
        proxy_pass http://cognidream_admin;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Health checks
    location /health {
        proxy_pass http://cognidream_production;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # Login endpoint
    location /login {
        proxy_pass http://cognidream_production;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

sshpass -p "$REMOTE_PASSWORD" scp -o StrictHostKeyChecking=no \
    /tmp/cognidream-nginx.conf \
    $REMOTE_USER@$REMOTE_HOST:/tmp/

sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'

# Install nginx config
mv /tmp/cognidream-nginx.conf /etc/nginx/sites-available/cognidream
ln -sf /etc/nginx/sites-available/cognidream /etc/nginx/sites-enabled/

# Remove default site
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Reload nginx
systemctl reload nginx
systemctl enable nginx

echo "✅ Nginx configured and reloaded"

ENDSSH

echo -e "${GREEN}✅ Nginx configured${NC}"

echo -e "${BLUE}[8/10]${NC} Creating systemd services..."

# Create systemd service files
for service in production mcp admin; do
    case $service in
        production)
            PORT=8090
            SCRIPT="api_server_production.py"
            ;;
        mcp)
            PORT=8091
            SCRIPT="mcp_server.py"
            ;;
        admin)
            PORT=8099
            SCRIPT="api_server_admin.py"
            ;;
    esac

    cat > /tmp/cognidream-$service.service << EOF
[Unit]
Description=CogniDream ${service^} Service
After=network.target

[Service]
Type=simple
User=cognidream
Group=cognidream
WorkingDirectory=/opt/cognidream/python
Environment="PATH=/opt/cognidream/venv/bin"
ExecStart=/opt/cognidream/venv/bin/python3 $SCRIPT
Restart=always
RestartSec=10
StandardOutput=append:/opt/cognidream/logs/${service}.log
StandardError=append:/opt/cognidream/logs/${service}.error.log

[Install]
WantedBy=multi-user.target
EOF

    sshpass -p "$REMOTE_PASSWORD" scp -o StrictHostKeyChecking=no \
        /tmp/cognidream-$service.service \
        $REMOTE_USER@$REMOTE_HOST:/tmp/
done

sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'

# Install systemd services
mv /tmp/cognidream-production.service /etc/systemd/system/
mv /tmp/cognidream-mcp.service /etc/systemd/system/
mv /tmp/cognidream-admin.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

echo "✅ Systemd services created"

ENDSSH

echo -e "${GREEN}✅ Systemd services created${NC}"

echo -e "${BLUE}[9/10]${NC} Starting services..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'

# Start and enable services
systemctl start cognidream-production
systemctl enable cognidream-production

systemctl start cognidream-mcp
systemctl enable cognidream-mcp

systemctl start cognidream-admin
systemctl enable cognidream-admin

sleep 5

# Check service status
echo "Service Status:"
systemctl is-active cognidream-production && echo "  ✅ Production API" || echo "  ❌ Production API"
systemctl is-active cognidream-mcp && echo "  ✅ MCP Server" || echo "  ❌ MCP Server"
systemctl is-active cognidream-admin && echo "  ✅ Admin API" || echo "  ❌ Admin API"

ENDSSH

echo -e "${GREEN}✅ Services started${NC}"

echo -e "${BLUE}[10/10]${NC} Verifying deployment..."
sleep 3

# Test endpoints
echo "Testing endpoints..."
if curl -s http://$REMOTE_HOST/health | grep -q "healthy"; then
    echo -e "${GREEN}✅ Production API responding${NC}"
else
    echo -e "${YELLOW}⚠️  Production API not responding yet (may need more time)${NC}"
fi

if curl -s http://$REMOTE_HOST/ | grep -q "DOCTYPE"; then
    echo -e "${GREEN}✅ Web interface accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Web interface not responding yet${NC}"
fi

# Cleanup
rm -f /tmp/cognidream-deploy.tar.gz
rm -f /tmp/cognidream-nginx.conf
rm -f /tmp/cognidream-*.service

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║              DEPLOYMENT COMPLETED SUCCESSFULLY!                  ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Access your platform at:"
echo -e "${GREEN}   http://$REMOTE_HOST${NC}"
echo ""
echo "📊 Service Status:"
echo "   View logs: ssh $REMOTE_USER@$REMOTE_HOST 'tail -f /opt/cognidream/logs/*.log'"
echo "   Check services: ssh $REMOTE_USER@$REMOTE_HOST 'systemctl status cognidream-*'"
echo ""
echo "🔐 Login Credentials:"
echo "   Username: user"
echo "   Password: Cogniware@2025"
echo "   (Change these in production!)"
echo ""
echo "📖 Management Commands:"
echo "   Restart: ssh $REMOTE_USER@$REMOTE_HOST 'systemctl restart cognidream-*'"
echo "   Stop: ssh $REMOTE_USER@$REMOTE_HOST 'systemctl stop cognidream-*'"
echo "   Logs: ssh $REMOTE_USER@$REMOTE_HOST 'journalctl -u cognidream-production -f'"
echo ""
echo "✨ Your CogniDream platform is now live!"
echo ""

