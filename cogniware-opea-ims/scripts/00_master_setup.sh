#!/bin/bash
################################################################################
# Cogniware Core - Master Setup Script
# Runs all setup scripts in sequence for complete installation
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

clear

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║       COGNIWARE CORE - MASTER SETUP & INSTALLATION               ║"
echo "║                                                                  ║"
echo "║              Complete Automated Installation                     ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

echo -e "${CYAN}This script will:${NC}"
echo "  1️⃣  Check system requirements"
echo "  2️⃣  Install dependencies"
echo "  3️⃣  Set up Cogniware services"
echo "  4️⃣  Start all services"
echo "  5️⃣  Verify installation"
echo "  6️⃣  (Optional) Build C++ engine"
echo ""

read -p "Continue with installation? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled."
    exit 0
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Check Requirements
echo -e "${BLUE}[1/6]${NC} ${CYAN}CHECKING REQUIREMENTS${NC}"
echo ""

bash "$SCRIPT_DIR/01_check_requirements.sh" || {
    echo -e "${RED}Requirements check failed!${NC}"
    echo "Please install missing requirements manually."
    exit 1
}

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 2: Install Requirements
echo -e "${BLUE}[2/6]${NC} ${CYAN}INSTALLING DEPENDENCIES${NC}"
echo ""

if [[ $EUID -eq 0 ]]; then
    bash "$SCRIPT_DIR/02_install_requirements.sh"
else
    bash "$SCRIPT_DIR/02_install_requirements.sh" --user-only
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 3: Setup Services
echo -e "${BLUE}[3/6]${NC} ${CYAN}SETTING UP SERVICES${NC}"
echo ""

bash "$SCRIPT_DIR/03_setup_services.sh"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 4: Services already started by step 3
echo -e "${BLUE}[4/6]${NC} ${CYAN}SERVICES STARTED${NC}"
echo -e "${GREEN}✅ All services started in previous step${NC}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 5: Verify Installation
echo -e "${BLUE}[5/6]${NC} ${CYAN}VERIFYING INSTALLATION${NC}"
echo ""

bash "$SCRIPT_DIR/06_verify_deliverables.sh"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 6: Optional C++ Build
echo -e "${BLUE}[6/6]${NC} ${CYAN}C++ ENGINE BUILD (Optional)${NC}"
echo ""

if [ -f "CMakeLists.txt" ]; then
    read -p "Build C++ inference engine? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        bash "$SCRIPT_DIR/07_build.sh"
        bash "$SCRIPT_DIR/08_test_build.sh"
    else
        echo "Skipping C++ build (can build later with ./scripts/07_build.sh)"
    fi
else
    echo "No CMakeLists.txt found, skipping C++ build"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Final Summary
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                                  ║${NC}"
echo -e "${GREEN}║          🎉 COGNIWARE CORE INSTALLATION COMPLETE! 🎉             ║${NC}"
echo -e "${GREEN}║                                                                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

echo "Installation Summary:"
echo "  ✅ Requirements checked and installed"
echo "  ✅ Python virtual environment configured"
echo "  ✅ All dependencies installed"
echo "  ✅ Services configured and started"
echo "  ✅ Installation verified"
echo ""

echo "🌐 Access Cogniware Core:"
echo "  Login Portal:  http://localhost:8000/login.html"
echo "  Admin Portal:  http://localhost:8000/admin-portal-enhanced.html"
echo "  User Portal:   http://localhost:8000/user-portal.html"
echo ""

echo "🔐 Default Credentials:"
echo "  Username: superadmin"
echo "  Password: Cogniware@2025"
echo "  ⚠️  CHANGE THIS PASSWORD IMMEDIATELY!"
echo ""

echo "📚 Documentation:"
echo "  README.md - Main guide"
echo "  DEFAULT_CREDENTIALS.md - All credentials"
echo "  docs/INDEX.md - Complete documentation index"
echo ""

echo "🛠️  Management:"
echo "  Start:  ./scripts/04_start_services.sh"
echo "  Stop:   ./scripts/05_stop_services.sh"
echo "  Verify: ./scripts/06_verify_deliverables.sh"
echo ""

echo "✨ Platform is ready! Open http://localhost:8000/login.html"
echo ""

