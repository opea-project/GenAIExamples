#!/bin/bash
################################################################################
# Cogniware Core - Build Script
# Builds the C++ inference engine
################################################################################

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║          COGNIWARE CORE - BUILD C++ ENGINE                       ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Create build directory
if [ -d "build" ]; then
    echo -e "${BLUE}Build directory exists, cleaning...${NC}"
    rm -rf build/*
else
    mkdir -p build
fi

cd build

# Configure
echo -e "${BLUE}Configuring with CMake...${NC}"
cmake .. -DCMAKE_BUILD_TYPE=Release

echo ""

# Build
echo -e "${BLUE}Building C++ engine...${NC}"
cmake --build . -j$(nproc)

echo ""

# Summary
if [ $? -eq 0 ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                  ║${NC}"
    echo -e "${GREEN}║              ✅ BUILD COMPLETED SUCCESSFULLY! ✅                  ║${NC}"
    echo -e "${GREEN}║                                                                  ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Build artifacts:"
    ls -lh *.so 2>/dev/null || echo "  (No .so files found)"
    echo ""
    echo "Next step:"
    echo "  ./scripts/08_test_build.sh"
    echo ""
    exit 0
else
    echo -e "${RED}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                                  ║${NC}"
    echo -e "${RED}║                  ❌ BUILD FAILED ❌                               ║${NC}"
    echo -e "${RED}║                                                                  ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    exit 1
fi

