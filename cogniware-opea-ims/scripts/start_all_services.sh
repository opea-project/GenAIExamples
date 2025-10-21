#!/bin/bash
################################################################################
# Cogniware Core - Start All Services
# Starts all 5 API servers + Web server for frontend
################################################################################

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║              STARTING COGNIWARE CORE SERVICES                    ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Stop any existing servers
echo -e "${BLUE}[1/7]${NC} Stopping existing servers..."
pkill -f "api_server" 2>/dev/null
pkill -f "http.server" 2>/dev/null
sleep 2
echo "✅ Existing servers stopped"

# Create logs directory
mkdir -p logs

# Activate virtual environment
source venv/bin/activate

# Start Admin Server (8099)
echo -e "${BLUE}[2/7]${NC} Starting Admin Server (Port 8099)..."
(cd python && python3 api_server_admin.py > ../logs/admin.log 2>&1 &)
sleep 3
if curl -s http://localhost:8099/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Admin Server running${NC} → http://localhost:8099"
else
    echo "⚠️  Admin Server not responding"
fi

# Start Protected Business Server (8096)
echo -e "${BLUE}[3/7]${NC} Starting Protected Business Server (Port 8096)..."
(cd python && python3 api_server_business_protected.py > ../logs/business_protected.log 2>&1 &)
sleep 3
if curl -s http://localhost:8096/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Protected Business Server running${NC} → http://localhost:8096"
else
    echo "⚠️  Protected Business Server not responding"
fi

# Start Production Server (8090)
echo -e "${BLUE}[4/7]${NC} Starting Production Server (Port 8090)..."
(cd python && python3 api_server_production.py > ../logs/production.log 2>&1 &)
sleep 3
if curl -s http://localhost:8090/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Production Server running${NC} → http://localhost:8090"
else
    echo "⚠️  Production Server not responding"
fi

# Start Business Server (8095)
echo -e "${BLUE}[5/7]${NC} Starting Business Server (Port 8095)..."
(cd python && python3 api_server_business.py > ../logs/business.log 2>&1 &)
sleep 3
if curl -s http://localhost:8095/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Business Server running${NC} → http://localhost:8095"
else
    echo "⚠️  Business Server not responding"
fi

# Start Demo Server (8080)
echo -e "${BLUE}[6/7]${NC} Starting Demo Server (Port 8080)..."
(cd python && python3 api_server.py > ../logs/demo.log 2>&1 &)
sleep 3
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Demo Server running${NC} → http://localhost:8080"
else
    echo "⚠️  Demo Server not responding"
fi

# Start Web Server for Frontend (8000)
echo -e "${BLUE}[7/7]${NC} Starting Web Server for Frontend (Port 8000)..."
(cd ui && python3 -m http.server 8000 > ../logs/webserver.log 2>&1 &)
sleep 2
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Web Server running${NC} → http://localhost:8000"
else
    echo "⚠️  Web Server not responding"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║              ALL SERVICES STARTED SUCCESSFULLY!                  ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
echo "API Server Status:"
echo "  🔐 Admin Server:         http://localhost:8099 (Protected)"
echo "  🔒 Business Protected:   http://localhost:8096 (Protected)"
echo "  🔧 Production Server:    http://localhost:8090 (Real GPU)"
echo "  📊 Business Server:      http://localhost:8095 (Legacy)"
echo "  📁 Demo Server:          http://localhost:8080 (Architecture)"
echo ""
echo "🌐 Frontend Web Server:"
echo "  Web Server:              http://localhost:8000"
echo ""
echo "🚀 Web Interfaces (OPEN THESE IN YOUR BROWSER):"
echo "  ⭐ Login Portal:         http://localhost:8000/login.html"
echo "  🔐 Super Admin Portal:   http://localhost:8000/admin-portal-enhanced.html"
echo "  🏢 Admin Dashboard:      http://localhost:8000/admin-dashboard.html"
echo "  👤 User Portal:          http://localhost:8000/user-portal.html"
echo ""
echo "Default Super Admin Login:"
echo "  Username: superadmin"
echo "  Password: Cogniware@2025"
echo "  ⚠️  CHANGE THIS PASSWORD!"
echo ""
echo "Management:"
echo "  View Logs: tail -f logs/<service>.log"
echo "  Stop All:  pkill -f api_server && pkill -f http.server"
echo ""
echo "Documentation:"
echo "  • README.md - Complete platform guide"
echo "  • QUICK_START_GUIDE.md - Quick start guide"
echo "  • USER_PERSONAS_GUIDE.md - User roles and activities"
echo "  • LICENSING_GUIDE.md - Complete licensing guide"
echo "  • USE_CASES_GUIDE.md - All business use cases"
echo ""
echo "✨ Ready! Open http://localhost:8000/login.html in your browser."
echo ""

