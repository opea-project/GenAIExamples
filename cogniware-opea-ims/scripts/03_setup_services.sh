#!/bin/bash
################################################################################
# Cogniware Core - Service Setup Script
# Sets up Cogniware as system services and starts all required services
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║          COGNIWARE CORE - SERVICE SETUP                          ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "Project Directory: $PROJECT_DIR"
echo ""

# Check if systemd is available
if command -v systemctl &> /dev/null && [[ $EUID -eq 0 ]]; then
    USE_SYSTEMD=true
    echo "✅ systemd detected - will create system services"
else
    USE_SYSTEMD=false
    echo "⚠️  Not root or no systemd - will use manual startup"
fi

echo ""

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
    echo "Run: ./scripts/02_install_requirements.sh first"
    exit 1
fi

echo ""

# Create systemd services if root
if [ "$USE_SYSTEMD" = true ]; then
    echo "Creating systemd services..."
    echo "-" | head -c 70; echo
    
    INSTALL_DIR="$PROJECT_DIR"
    VENV_DIR="$INSTALL_DIR/venv"
    SERVICE_USER=$(whoami)
    
    # Admin Server
    cat > /etc/systemd/system/cogniware-admin.service << EOF
[Unit]
Description=Cogniware Core - Admin Server
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR/python
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$VENV_DIR/bin/python3 $INSTALL_DIR/python/api_server_admin.py
Restart=always
RestartSec=10
StandardOutput=append:$INSTALL_DIR/logs/admin.log
StandardError=append:$INSTALL_DIR/logs/admin-error.log

[Install]
WantedBy=multi-user.target
EOF

    # Production Server
    cat > /etc/systemd/system/cogniware-production.service << EOF
[Unit]
Description=Cogniware Core - Production Server
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR/python
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$VENV_DIR/bin/python3 $INSTALL_DIR/python/api_server_production.py
Restart=always
RestartSec=10
StandardOutput=append:$INSTALL_DIR/logs/production.log
StandardError=append:$INSTALL_DIR/logs/production-error.log

[Install]
WantedBy=multi-user.target
EOF

    # Business Protected Server
    cat > /etc/systemd/system/cogniware-business-protected.service << EOF
[Unit]
Description=Cogniware Core - Business Protected Server
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR/python
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$VENV_DIR/bin/python3 $INSTALL_DIR/python/api_server_business_protected.py
Restart=always
RestartSec=10
StandardOutput=append:$INSTALL_DIR/logs/business-protected.log
StandardError=append:$INSTALL_DIR/logs/business-protected-error.log

[Install]
WantedBy=multi-user.target
EOF

    # Web Server
    cat > /etc/systemd/system/cogniware-webserver.service << EOF
[Unit]
Description=Cogniware Core - Web Server
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR/ui
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$VENV_DIR/bin/python3 -m http.server 8000
Restart=always
RestartSec=10
StandardOutput=append:$INSTALL_DIR/logs/webserver.log
StandardError=append:$INSTALL_DIR/logs/webserver-error.log

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    systemctl daemon-reload
    echo "✅ systemd services created"
    
    # Enable services
    echo ""
    echo "Enabling services to start on boot..."
    systemctl enable cogniware-admin.service
    systemctl enable cogniware-production.service
    systemctl enable cogniware-business-protected.service
    systemctl enable cogniware-webserver.service
    echo "✅ Services enabled"
    
    # Start services
    echo ""
    echo "Starting services..."
    systemctl start cogniware-admin.service
    systemctl start cogniware-production.service
    systemctl start cogniware-business-protected.service
    systemctl start cogniware-webserver.service
    
    sleep 5
    
    # Check status
    echo ""
    echo "Service Status:"
    echo "-" | head -c 70; echo
    systemctl is-active --quiet cogniware-admin.service && echo -e "${GREEN}✅ Admin Server${NC}" || echo -e "${RED}❌ Admin Server${NC}"
    systemctl is-active --quiet cogniware-production.service && echo -e "${GREEN}✅ Production Server${NC}" || echo -e "${RED}❌ Production Server${NC}"
    systemctl is-active --quiet cogniware-business-protected.service && echo -e "${GREEN}✅ Business Protected Server${NC}" || echo -e "${RED}❌ Business Protected Server${NC}"
    systemctl is-active --quiet cogniware-webserver.service && echo -e "${GREEN}✅ Web Server${NC}" || echo -e "${RED}❌ Web Server${NC}"
    
else
    # Manual startup
    echo "Starting services manually..."
    echo "-" | head -c 70; echo
    
    # Create logs directory
    mkdir -p logs
    
    # Start services
    (cd python && python3 api_server_admin.py > ../logs/admin.log 2>&1 &)
    echo "✅ Started Admin Server (8099)"
    sleep 2
    
    (cd python && python3 api_server_production.py > ../logs/production.log 2>&1 &)
    echo "✅ Started Production Server (8090)"
    sleep 2
    
    (cd python && python3 api_server_business_protected.py > ../logs/business-protected.log 2>&1 &)
    echo "✅ Started Business Protected Server (8096)"
    sleep 2
    
    (cd ui && python3 -m http.server 8000 > ../logs/webserver.log 2>&1 &)
    echo "✅ Started Web Server (8000)"
    sleep 3
    
    # Verify
    echo ""
    echo "Verifying services..."
    curl -s http://localhost:8099/health > /dev/null && echo -e "${GREEN}✅ Admin Server responding${NC}" || echo -e "${RED}❌ Admin Server not responding${NC}"
    curl -s http://localhost:8090/health > /dev/null && echo -e "${GREEN}✅ Production Server responding${NC}" || echo -e "${RED}❌ Production Server not responding${NC}"
    curl -s http://localhost:8000/ > /dev/null && echo -e "${GREEN}✅ Web Server responding${NC}" || echo -e "${RED}❌ Web Server not responding${NC}"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║             COGNIWARE SERVICES STARTED SUCCESSFULLY!             ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

echo "Access Points:"
echo "  🌐 Web Portal:      http://localhost:8000/login.html"
echo "  🔐 Admin API:       http://localhost:8099"
echo "  🚀 Production API:  http://localhost:8090"
echo "  🔒 Business API:    http://localhost:8096"
echo ""

echo "Default Credentials:"
echo "  Username: superadmin"
echo "  Password: Cogniware@2025"
echo "  ⚠️  CHANGE THIS PASSWORD!"
echo ""

if [ "$USE_SYSTEMD" = true ]; then
    echo "Service Management:"
    echo "  systemctl status cogniware-admin"
    echo "  systemctl stop cogniware-admin"
    echo "  systemctl restart cogniware-admin"
    echo "  journalctl -u cogniware-admin -f"
else
    echo "Service Management:"
    echo "  ./scripts/04_start_services.sh"
    echo "  ./scripts/05_stop_services.sh"
    echo "  tail -f logs/*.log"
fi

echo ""
echo "Documentation:"
echo "  README.md - Main guide"
echo "  DEFAULT_CREDENTIALS.md - All credentials"
echo "  docs/INDEX.md - Complete documentation index"
echo ""

