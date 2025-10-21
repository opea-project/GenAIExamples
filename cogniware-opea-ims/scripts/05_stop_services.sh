#!/bin/bash
################################################################################
# Cogniware Core - Stop All Services
# Stops all running Cogniware services
################################################################################

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║              STOPPING COGNIWARE CORE SERVICES                    ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Check for systemd
if command -v systemctl &> /dev/null && [ -f /etc/systemd/system/cogniware-admin.service ]; then
    echo "Stopping systemd services..."
    echo ""
    
    sudo systemctl stop cogniware-admin.service 2>/dev/null || true
    sudo systemctl stop cogniware-production.service 2>/dev/null || true
    sudo systemctl stop cogniware-business-protected.service 2>/dev/null || true
    sudo systemctl stop cogniware-webserver.service 2>/dev/null || true
    
    sleep 2
    
    echo -e "${GREEN}✅ All systemd services stopped${NC}"
    
else
    echo "Stopping manual processes..."
    echo ""
    
    # Kill all API servers
    pkill -f "api_server" 2>/dev/null || true
    pkill -f "mcp_server" 2>/dev/null || true
    pkill -f "http.server" 2>/dev/null || true
    
    sleep 2
    
    # Verify stopped
    if ps aux | grep -E "(api_server|http.server)" | grep -v grep > /dev/null; then
        echo -e "${YELLOW}⚠️  Some processes may still be running${NC}"
        echo "Force kill? (y/N)"
        read -n 1 -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            pkill -9 -f "api_server" 2>/dev/null || true
            pkill -9 -f "http.server" 2>/dev/null || true
            echo -e "${GREEN}✅ Force killed all processes${NC}"
        fi
    else
        echo -e "${GREEN}✅ All processes stopped${NC}"
    fi
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║              ALL SERVICES STOPPED SUCCESSFULLY!                  ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

echo "To start services again:"
echo "  ./scripts/04_start_services.sh"
echo ""

