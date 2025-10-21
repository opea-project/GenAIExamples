#!/bin/bash
################################################################################
# Cogniware Core - Start All Services
# Starts all 6 Cogniware services (5 API servers + Web server)
################################################################################

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║              STARTING COGNIWARE CORE SERVICES                    ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Check for systemd
if command -v systemctl &> /dev/null && [ -f /etc/systemd/system/cogniware-admin.service ]; then
    echo "Using systemd services..."
    echo ""
    
    sudo systemctl start cogniware-admin.service
    sudo systemctl start cogniware-production.service
    sudo systemctl start cogniware-business-protected.service
    sudo systemctl start cogniware-webserver.service
    
    sleep 3
    
    echo "Service Status:"
    sudo systemctl is-active --quiet cogniware-admin.service && echo -e "${GREEN}✅ Admin Server${NC}" || echo -e "${RED}❌ Admin Server${NC}"
    sudo systemctl is-active --quiet cogniware-production.service && echo -e "${GREEN}✅ Production Server${NC}" || echo -e "${RED}❌ Production Server${NC}"
    sudo systemctl is-active --quiet cogniware-business-protected.service && echo -e "${GREEN}✅ Business Protected${NC}" || echo -e "${RED}❌ Business Protected${NC}"
    sudo systemctl is-active --quiet cogniware-webserver.service && echo -e "${GREEN}✅ Web Server${NC}" || echo -e "${RED}❌ Web Server${NC}"
    
else
    echo "Using manual service startup..."
    echo ""
    
    # Create logs directory
    mkdir -p logs
    
    # Activate virtual environment
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}❌ Virtual environment not found${NC}"
        echo "Run: ./scripts/02_install_requirements.sh first"
        exit 1
    fi
    
    # Start services
    echo -e "${BLUE}[1/6]${NC} Starting Admin Server (Port 8099)..."
    (cd python && python3 api_server_admin.py > ../logs/admin.log 2>&1 &)
    sleep 3
    curl -s http://localhost:8099/health > /dev/null && echo -e "${GREEN}✅ Admin Server running${NC}" || echo -e "${RED}❌ Admin Server not responding${NC}"
    
    echo -e "${BLUE}[2/6]${NC} Starting Business Protected Server (Port 8096)..."
    (cd python && python3 api_server_business_protected.py > ../logs/business-protected.log 2>&1 &)
    sleep 3
    curl -s http://localhost:8096/health > /dev/null && echo -e "${GREEN}✅ Business Protected running${NC}" || echo -e "${RED}❌ Business Protected not responding${NC}"
    
    echo -e "${BLUE}[3/6]${NC} Starting Production Server (Port 8090)..."
    (cd python && python3 api_server_production.py > ../logs/production.log 2>&1 &)
    sleep 3
    curl -s http://localhost:8090/health > /dev/null && echo -e "${GREEN}✅ Production Server running${NC}" || echo -e "${RED}❌ Production Server not responding${NC}"
    
    echo -e "${BLUE}[4/6]${NC} Starting Business Server (Port 8095)..."
    (cd python && python3 api_server_business.py > ../logs/business.log 2>&1 &)
    sleep 3
    curl -s http://localhost:8095/health > /dev/null && echo -e "${GREEN}✅ Business Server running${NC}" || echo -e "${RED}❌ Business Server not responding${NC}"
    
    echo -e "${BLUE}[5/6]${NC} Starting Demo Server (Port 8080)..."
    (cd python && python3 api_server.py > ../logs/demo.log 2>&1 &)
    sleep 3
    curl -s http://localhost:8080/health > /dev/null && echo -e "${GREEN}✅ Demo Server running${NC}" || echo -e "${RED}❌ Demo Server not responding${NC}"
    
    echo -e "${BLUE}[6/7]${NC} Starting MCP Server (Port 8091)..."
    (cd python && python3 mcp_server.py > ../logs/mcp.log 2>&1 &)
    sleep 2
    curl -s http://localhost:8091/mcp/health > /dev/null && echo -e "${GREEN}✅ MCP Server running${NC}" || echo -e "${RED}❌ MCP Server not responding${NC}"
    
    echo -e "${BLUE}[7/7]${NC} Starting Web Server (Port 8000)..."
    (cd ui && python3 -m http.server 8000 > ../logs/webserver.log 2>&1 &)
    sleep 2
    curl -s http://localhost:8000/ > /dev/null && echo -e "${GREEN}✅ Web Server running${NC}" || echo -e "${RED}❌ Web Server not responding${NC}"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║              ALL SERVICES STARTED SUCCESSFULLY!                  ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

echo "🌐 Access Cogniware Core:"
echo "  Login Portal:  http://localhost:8000/login.html"
echo "  Admin Portal:  http://localhost:8000/admin-portal-enhanced.html"
echo "  Chat Portal:   http://localhost:8000/user-portal-chat.html"
echo "  Code IDE:      http://localhost:8000/code-ide.html"
echo ""

echo "🔐 Default Credentials:"
echo "  Username: superadmin"
echo "  Password: Cogniware@2025"
echo "  ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!"
echo ""

echo "📚 Documentation:"
echo "  DEFAULT_CREDENTIALS.md - All login credentials"
echo "  README.md - Complete platform guide"
echo "  docs/INDEX.md - Documentation index"
echo ""

echo "🛠️  Management:"
if [ "$USE_SYSTEMD" = true ]; then
    echo "  systemctl status cogniware-admin"
    echo "  systemctl stop cogniware-admin"
    echo "  journalctl -u cogniware-admin -f"
else
    echo "  ./scripts/05_stop_services.sh - Stop all services"
    echo "  tail -f logs/*.log - View logs"
fi

echo ""
echo "✨ Ready! Open http://localhost:8000/login.html in your browser."
echo ""

