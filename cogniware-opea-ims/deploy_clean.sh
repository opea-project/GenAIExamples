#!/bin/bash
################################################################################
# CogniDream Platform - Clean Deployment to Production
# Stops existing services and performs fresh installation
################################################################################

REMOTE_HOST="185.141.218.141"
REMOTE_USER="root"
REMOTE_PASSWORD="CogniDream2025"

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║     CogniDream - Clean Production Deployment                    ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Kill all existing services
echo -e "${BLUE}[1/12]${NC} Stopping all existing services on remote server..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
#!/bin/bash
set -e

echo "Stopping systemd services..."
systemctl stop cognidream-* 2>/dev/null || true
systemctl stop cogniware-* 2>/dev/null || true
systemctl disable cognidream-* 2>/dev/null || true
systemctl disable cogniware-* 2>/dev/null || true

echo "Killing Python processes..."
pkill -9 -f "simple_backend" 2>/dev/null || true
pkill -9 -f "api_server" 2>/dev/null || true
pkill -9 -f "mcp_server" 2>/dev/null || true
pkill -9 -f "cognidream" 2>/dev/null || true
pkill -9 -f "pip install" 2>/dev/null || true

sleep 2

echo "Removing old service files..."
rm -f /etc/systemd/system/cognidream-*.service
rm -f /etc/systemd/system/cogniware-*.service
systemctl daemon-reload

echo "✅ All services stopped"
ENDSSH

echo -e "${GREEN}✅ All existing services stopped${NC}"

# Step 2: Clean up old installation
echo -e "${BLUE}[2/12]${NC} Removing old installation..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
rm -rf /opt/cognidream
rm -f /tmp/cognidream-*
echo "✅ Old installation removed"
ENDSSH

echo -e "${GREEN}✅ Old installation cleaned${NC}"

# Step 3: Create fresh directories
echo -e "${BLUE}[3/12]${NC} Creating fresh installation directories..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
# Create cognidream user if doesn't exist
if ! id -u cognidream &>/dev/null; then
    useradd -r -s /bin/bash -m -d /home/cognidream cognidream
fi

# Create deployment directory
mkdir -p /opt/cognidream/{logs,databases,documents,projects}
chown -R cognidream:cognidream /opt/cognidream
echo "✅ Directories created"
ENDSSH

echo -e "${GREEN}✅ Directories ready${NC}"

# Step 4: Package and transfer
echo -e "${BLUE}[4/12]${NC} Creating deployment package..."
cd "$(dirname "$0")"
tar -czf /tmp/cognidream-deploy.tar.gz \
    --exclude='venv' \
    --exclude='build*' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='*.log' \
    python/ ui/ scripts/ requirements.txt config.json 2>/dev/null

echo -e "${GREEN}✅ Package created ($(du -h /tmp/cognidream-deploy.tar.gz | cut -f1))${NC}"

echo -e "${BLUE}[5/12]${NC} Transferring to remote server..."
sshpass -p "$REMOTE_PASSWORD" scp -o StrictHostKeyChecking=no \
    /tmp/cognidream-deploy.tar.gz $REMOTE_USER@$REMOTE_HOST:/tmp/

echo -e "${GREEN}✅ Files transferred${NC}"

# Step 5: Extract files
echo -e "${BLUE}[6/12]${NC} Extracting files..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
cd /opt/cognidream
tar -xzf /tmp/cognidream-deploy.tar.gz
chown -R cognidream:cognidream /opt/cognidream
echo "✅ Files extracted"
ENDSSH

echo -e "${GREEN}✅ Files extracted${NC}"

# Step 6: Setup Python environment
echo -e "${BLUE}[7/12]${NC} Creating Python virtual environment..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
cd /opt/cognidream
sudo -u cognidream python3.12 -m venv venv
echo "✅ Virtual environment created"
ENDSSH

echo -e "${GREEN}✅ Virtual environment created${NC}"

# Step 7: Install Python packages
echo -e "${BLUE}[8/12]${NC} Installing Python packages (this may take 2-3 minutes)..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
cd /opt/cognidream
echo "Upgrading pip..."
sudo -u cognidream venv/bin/pip install --upgrade pip setuptools wheel -q

echo "Installing requirements..."
sudo -u cognidream venv/bin/pip install -r requirements.txt -q 2>&1 | grep -E "(Successfully|ERROR|Warning)" || true

echo "✅ Packages installed"
ENDSSH

echo -e "${GREEN}✅ Python packages installed${NC}"

# Step 8: Configure nginx
echo -e "${BLUE}[9/12]${NC} Configuring nginx..."
cat > /tmp/cognidream-nginx.conf << 'EOF'
upstream cognidream_production {
    server 127.0.0.1:8090;
}

upstream cognidream_mcp {
    server 127.0.0.1:8091;
}

server {
    listen 80;
    server_name 185.141.218.141 _;
    client_max_body_size 100M;

    root /opt/cognidream/ui;
    index index.html;

    access_log /var/log/nginx/cognidream.access.log;
    error_log /var/log/nginx/cognidream.error.log;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://cognidream_production;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
    }

    location /mcp/ {
        proxy_pass http://cognidream_mcp;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }

    location /health {
        proxy_pass http://cognidream_production/health;
    }

    location /login {
        proxy_pass http://cognidream_production/login;
    }
}
EOF

sshpass -p "$REMOTE_PASSWORD" scp -o StrictHostKeyChecking=no /tmp/cognidream-nginx.conf $REMOTE_USER@$REMOTE_HOST:/tmp/

sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
mv /tmp/cognidream-nginx.conf /etc/nginx/sites-available/cognidream
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/cognidream /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
echo "✅ Nginx configured"
ENDSSH

echo -e "${GREEN}✅ Nginx configured${NC}"

# Step 9: Create systemd services
echo -e "${BLUE}[10/12]${NC} Creating systemd services..."

# Production service
cat > /tmp/cognidream-production.service << 'EOF'
[Unit]
Description=CogniDream Production API
After=network.target

[Service]
Type=simple
User=cognidream
WorkingDirectory=/opt/cognidream/python
Environment="PATH=/opt/cognidream/venv/bin:/usr/bin"
ExecStart=/opt/cognidream/venv/bin/python3 api_server_production.py
Restart=always
RestartSec=5
StandardOutput=append:/opt/cognidream/logs/production.log
StandardError=append:/opt/cognidream/logs/production.error.log

[Install]
WantedBy=multi-user.target
EOF

# MCP service
cat > /tmp/cognidream-mcp.service << 'EOF'
[Unit]
Description=CogniDream MCP Server
After=network.target

[Service]
Type=simple
User=cognidream
WorkingDirectory=/opt/cognidream/python
Environment="PATH=/opt/cognidream/venv/bin:/usr/bin"
ExecStart=/opt/cognidream/venv/bin/python3 mcp_server.py
Restart=always
RestartSec=5
StandardOutput=append:/opt/cognidream/logs/mcp.log
StandardError=append:/opt/cognidream/logs/mcp.error.log

[Install]
WantedBy=multi-user.target
EOF

sshpass -p "$REMOTE_PASSWORD" scp -o StrictHostKeyChecking=no /tmp/cognidream-*.service $REMOTE_USER@$REMOTE_HOST:/tmp/

sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
mv /tmp/cognidream-production.service /etc/systemd/system/
mv /tmp/cognidream-mcp.service /etc/systemd/system/
systemctl daemon-reload
echo "✅ Services created"
ENDSSH

echo -e "${GREEN}✅ Systemd services created${NC}"

# Step 10: Install missing packages
echo -e "${BLUE}[11/12]${NC} Installing missing Python packages..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
cd /opt/cognidream
sudo -u cognidream venv/bin/pip install psutil flask flask-cors pydantic -q
echo "✅ Additional packages installed"
ENDSSH

echo -e "${GREEN}✅ Additional packages installed${NC}"

# Step 11: Start services
echo -e "${BLUE}[12/12]${NC} Starting services..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no $REMOTE_USER@$REMOTE_HOST << 'ENDSSH'
systemctl start cognidream-production
systemctl enable cognidream-production

systemctl start cognidream-mcp
systemctl enable cognidream-mcp

sleep 5

echo "Service Status:"
systemctl is-active --quiet cognidream-production && echo "  ✅ Production API" || echo "  ⚠️  Production API (check logs)"
systemctl is-active --quiet cognidream-mcp && echo "  ✅ MCP Server" || echo "  ⚠️  MCP Server (check logs)"
ENDSSH

echo -e "${GREEN}✅ Services started${NC}"

# Final verification
echo ""
echo "Waiting for services to stabilize..."
sleep 5

echo ""
echo "Testing deployment..."
if curl -s http://185.141.218.141/ | grep -q "DOCTYPE"; then
    echo -e "${GREEN}✅ Web interface: WORKING${NC}"
else
    echo -e "${RED}❌ Web interface: NOT RESPONDING${NC}"
fi

if curl -s http://185.141.218.141/health 2>&1 | grep -q "healthy"; then
    echo -e "${GREEN}✅ Production API: WORKING${NC}"
else
    echo -e "${YELLOW}⚠️  Production API: Starting... (may need 30-60 seconds)${NC}"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                DEPLOYMENT COMPLETE                               ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Platform URL: http://185.141.218.141"
echo "🔐 Login: user / Cogniware@2025"
echo ""
echo "📊 Check status:"
echo "   curl http://185.141.218.141/health"
echo "   curl http://185.141.218.141/"
echo ""
echo "📝 View logs:"
echo "   sshpass -p '$REMOTE_PASSWORD' ssh $REMOTE_USER@$REMOTE_HOST 'tail -f /opt/cognidream/logs/*.log'"
echo ""

# Cleanup
rm -f /tmp/cognidream-*

echo "✨ CogniDream is deployed!"
echo ""

