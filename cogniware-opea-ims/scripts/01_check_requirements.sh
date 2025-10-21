#!/bin/bash
################################################################################
# Cogniware Core - Requirements Checker
# Checks all platform dependencies and system requirements
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
echo "║          COGNIWARE CORE - REQUIREMENTS CHECKER                   ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

ISSUES=0
WARNINGS=0

check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✅ $2${NC}"
        return 0
    else
        echo -e "${RED}❌ $2 - NOT FOUND${NC}"
        ((ISSUES++))
        return 1
    fi
}

check_optional() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${YELLOW}⚠️  $2 - Optional but recommended${NC}"
        ((WARNINGS++))
    fi
}

check_python_package() {
    if python3 -c "import $1" 2>/dev/null; then
        echo -e "${GREEN}✅ Python: $2${NC}"
    else
        echo -e "${RED}❌ Python: $2 - NOT INSTALLED${NC}"
        ((ISSUES++))
    fi
}

# System Info
echo "System Information:"
echo "-" | head -c 70; echo
uname -a
echo ""

# Check OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "OS: $NAME $VERSION"
else
    echo -e "${RED}Cannot detect OS${NC}"
fi
echo ""

# Core Requirements
echo "Core Requirements:"
echo "-" | head -c 70; echo
check_command "python3" "Python 3"
check_command "pip3" "pip (Python package manager)"
check_command "git" "Git"
check_command "curl" "cURL"
check_command "cmake" "CMake"
check_command "gcc" "GCC Compiler"
check_command "g++" "G++ Compiler"
echo ""

# Python Version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ $MAJOR -eq 3 ] && [ $MINOR -ge 9 ]; then
        echo -e "${GREEN}✅ Python Version: $PYTHON_VERSION (>= 3.9 required)${NC}"
    else
        echo -e "${RED}❌ Python Version: $PYTHON_VERSION (>= 3.9 required)${NC}"
        ((ISSUES++))
    fi
fi
echo ""

# Python Packages
echo "Python Packages:"
echo "-" | head -c 70; echo
check_python_package "flask" "Flask"
check_python_package "flask_cors" "Flask-CORS"
check_python_package "requests" "Requests"
check_python_package "psutil" "psutil"
check_python_package "sqlite3" "SQLite3"
echo ""

# Optional but recommended
echo "Optional Components:"
echo "-" | head -c 70; echo
check_optional "nvidia-smi" "NVIDIA GPU"
check_optional "nvcc" "CUDA Toolkit"
check_optional "docker" "Docker"
check_optional "systemctl" "systemd"
echo ""

# GPU Detection
echo "GPU Detection:"
echo "-" | head -c 70; echo
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader | head -1
    echo -e "${GREEN}✅ NVIDIA GPU detected and working${NC}"
else
    echo -e "${YELLOW}⚠️  No NVIDIA GPU detected - CPU mode will be used${NC}"
    ((WARNINGS++))
fi
echo ""

# Disk Space
echo "Disk Space:"
echo "-" | head -c 70; echo
AVAILABLE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ $AVAILABLE -ge 100 ]; then
    echo -e "${GREEN}✅ Available: ${AVAILABLE}GB (>= 100GB recommended)${NC}"
elif [ $AVAILABLE -ge 50 ]; then
    echo -e "${YELLOW}⚠️  Available: ${AVAILABLE}GB (>= 100GB recommended)${NC}"
    ((WARNINGS++))
else
    echo -e "${RED}❌ Available: ${AVAILABLE}GB (< 50GB minimum required)${NC}"
    ((ISSUES++))
fi
echo ""

# Memory
echo "System Memory:"
echo "-" | head -c 70; echo
TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
if [ $TOTAL_MEM -ge 16 ]; then
    echo -e "${GREEN}✅ RAM: ${TOTAL_MEM}GB (>= 16GB recommended)${NC}"
elif [ $TOTAL_MEM -ge 8 ]; then
    echo -e "${YELLOW}⚠️  RAM: ${TOTAL_MEM}GB (>= 16GB recommended)${NC}"
    ((WARNINGS++))
else
    echo -e "${RED}❌ RAM: ${TOTAL_MEM}GB (< 8GB minimum required)${NC}"
    ((ISSUES++))
fi
echo ""

# Ports
echo "Port Availability:"
echo "-" | head -c 70; echo
for PORT in 8080 8090 8095 8096 8099 8000; do
    if ! netstat -tuln 2>/dev/null | grep ":$PORT " > /dev/null; then
        echo -e "${GREEN}✅ Port $PORT available${NC}"
    else
        echo -e "${YELLOW}⚠️  Port $PORT in use${NC}"
        ((WARNINGS++))
    fi
done
echo ""

# Summary
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                        SUMMARY                                   ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

if [ $ISSUES -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL REQUIREMENTS MET!${NC}"
    echo "System is ready for Cogniware Core installation."
    EXIT_CODE=0
elif [ $ISSUES -eq 0 ]; then
    echo -e "${YELLOW}⚠️  SYSTEM READY WITH WARNINGS${NC}"
    echo "Issues: $ISSUES | Warnings: $WARNINGS"
    echo "System can run but some features may not work optimally."
    EXIT_CODE=0
else
    echo -e "${RED}❌ REQUIREMENTS NOT MET${NC}"
    echo "Critical Issues: $ISSUES | Warnings: $WARNINGS"
    echo "Please install missing requirements before proceeding."
    EXIT_CODE=1
fi

echo ""
exit $EXIT_CODE

