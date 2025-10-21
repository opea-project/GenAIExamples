#!/bin/bash
################################################################################
# Cogniware Core - Requirements Installer
# Installs all platform dependencies with skip-if-exists logic
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
echo "║        COGNIWARE CORE - REQUIREMENTS INSTALLER                   ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Check if running as root for system packages
if [[ $EUID -ne 0 ]] && [[ "$1" != "--user-only" ]]; then
    echo -e "${YELLOW}Warning: Not running as root.${NC}"
    echo "System packages cannot be installed without sudo."
    echo "Run with: sudo $0"
    echo "Or run with: $0 --user-only (for Python packages only)"
    echo ""
    read -p "Continue with Python packages only? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    USER_ONLY=true
else
    USER_ONLY=false
fi

install_if_missing() {
    PACKAGE=$1
    DESCRIPTION=$2
    
    if command -v $PACKAGE &> /dev/null; then
        echo -e "${BLUE}⏭️  $DESCRIPTION already installed${NC}"
        return 0
    else
        echo -e "${YELLOW}📦 Installing $DESCRIPTION...${NC}"
        return 1
    fi
}

# System packages
if [ "$USER_ONLY" = false ]; then
    echo "Installing System Packages..."
    echo "-" | head -c 70; echo
    
    apt-get update -qq || true
    
    # Core development tools
    if ! install_if_missing "gcc" "GCC Compiler"; then
        apt-get install -y build-essential
    fi
    
    if ! install_if_missing "cmake" "CMake"; then
        apt-get install -y cmake
    fi
    
    if ! install_if_missing "git" "Git"; then
        apt-get install -y git
    fi
    
    if ! install_if_missing "curl" "cURL"; then
        apt-get install -y curl wget
    fi
    
    if ! install_if_missing "python3" "Python 3"; then
        apt-get install -y python3 python3-pip python3-venv python3-dev
    fi
    
    # Optional but recommended
    if ! command -v nvidia-smi &> /dev/null; then
        echo -e "${YELLOW}⚠️  NVIDIA drivers not found (optional)${NC}"
        read -p "Install NVIDIA drivers? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            apt-get install -y nvidia-driver-535 || echo "Failed to install NVIDIA drivers"
        fi
    else
        echo -e "${BLUE}⏭️  NVIDIA drivers already installed${NC}"
    fi
    
    echo -e "${GREEN}✅ System packages installation complete${NC}"
    echo ""
fi

# Python virtual environment
echo "Setting up Python Virtual Environment..."
echo "-" | head -c 70; echo

if [ -d "venv" ]; then
    echo -e "${BLUE}⏭️  Virtual environment already exists${NC}"
else
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate venv
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}📦 Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel -q

echo ""

# Python packages
echo "Installing Python Packages..."
echo "-" | head -c 70; echo

# Check requirements.txt
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}📦 Installing from requirements.txt...${NC}"
    pip install -r requirements.txt -q
    echo -e "${GREEN}✅ Requirements installed${NC}"
else
    echo -e "${YELLOW}No requirements.txt found, installing core packages...${NC}"
    
    # Core packages
    PACKAGES=(
        "flask"
        "flask-cors"
        "requests"
        "psutil"
        "pynvml"
        "nvidia-ml-py3"
    )
    
    for pkg in "${PACKAGES[@]}"; do
        if python3 -c "import ${pkg//-/_}" 2>/dev/null; then
            echo -e "${BLUE}⏭️  $pkg already installed${NC}"
        else
            echo -e "${YELLOW}📦 Installing $pkg...${NC}"
            pip install $pkg -q
        fi
    done
    
    echo -e "${GREEN}✅ Core packages installed${NC}"
fi

echo ""

# Verify installation
echo "Verification:"
echo "-" | head -c 70; echo

CRITICAL_PACKAGES=("flask" "requests" "psutil")
ALL_OK=true

for pkg in "${CRITICAL_PACKAGES[@]}"; do
    if python3 -c "import ${pkg//-/_}" 2>/dev/null; then
        echo -e "${GREEN}✅ ${pkg}${NC}"
    else
        echo -e "${RED}❌ ${pkg} - FAILED TO INSTALL${NC}"
        ALL_OK=false
    fi
done

echo ""

if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                  ║${NC}"
    echo -e "${GREEN}║             ALL REQUIREMENTS INSTALLED SUCCESSFULLY!             ║${NC}"
    echo -e "${GREEN}║                                                                  ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run: ./scripts/03_setup_services.sh"
    echo "  2. Or run: ./scripts/00_master_setup.sh (for complete setup)"
    echo ""
    exit 0
else
    echo -e "${RED}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                                  ║${NC}"
    echo -e "${RED}║             SOME REQUIREMENTS FAILED TO INSTALL!                 ║${NC}"
    echo -e "${RED}║                                                                  ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Please fix the errors above and run again."
    echo ""
    exit 1
fi

