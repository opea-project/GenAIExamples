#!/bin/bash
################################################################################
# Cogniware Core - Test Build Script
# Tests the compiled C++ engine
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
echo "║          COGNIWARE CORE - TEST BUILD                             ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Check if build exists
if [ ! -d "build" ]; then
    echo -e "${RED}❌ Build directory not found${NC}"
    echo "Run: ./scripts/07_build.sh first"
    exit 1
fi

cd build

# Run tests if available
if [ -f "simple_engine_test" ]; then
    echo -e "${BLUE}Running C++ tests...${NC}"
    ./simple_engine_test
    echo ""
fi

# Test Python bindings
echo -e "${BLUE}Testing Python bindings...${NC}"
cd "$PROJECT_DIR"

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

if [ -f "test_build.py" ]; then
    python3 test_build.py
else
    echo -e "${YELLOW}⚠️  test_build.py not found, skipping Python binding test${NC}"
fi

echo ""

# Summary
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                                  ║${NC}"
echo -e "${GREEN}║              ✅ BUILD TESTS COMPLETED! ✅                         ║${NC}"
echo -e "${GREEN}║                                                                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

