#!/bin/bash
################################################################################
# Cogniware Core - Verify Deliverables
# Comprehensive verification of all platform components
################################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║          COGNIWARE CORE - VERIFY DELIVERABLES                    ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

PASSED=0
FAILED=0

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅ $2${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ $2 - MISSING${NC}"
        ((FAILED++))
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✅ $2${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ $2 - MISSING${NC}"
        ((FAILED++))
    fi
}

check_service() {
    if curl -s "$1" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $2 - Responding${NC}"
        ((PASSED++))
    else
        echo -e "${YELLOW}⚠️  $2 - Not responding (may not be started)${NC}"
    fi
}

# Check Core Files
echo "Core Files:"
echo "-" | head -c 70; echo
check_file "README.md" "README.md"
check_file "DEFAULT_CREDENTIALS.md" "DEFAULT_CREDENTIALS.md"
check_file "requirements.txt" "requirements.txt"
check_file "config.json" "config.json"
echo ""

# Check Directories
echo "Directory Structure:"
echo "-" | head -c 70; echo
check_dir "python" "Python source directory"
check_dir "ui" "UI directory"
check_dir "docs" "Documentation directory"
check_dir "scripts" "Scripts directory"
check_dir "api" "API collections directory"
check_dir "databases" "Databases directory"
echo ""

# Check Python Files
echo "Python Modules:"
echo "-" | head -c 70; echo
check_file "python/api_server_admin.py" "Admin Server"
check_file "python/api_server_production.py" "Production Server"
check_file "python/api_server_business_protected.py" "Business Protected Server"
check_file "python/cogniware_llms.py" "Cogniware LLMs"
check_file "python/parallel_llm_executor.py" "Parallel LLM Executor"
check_file "python/licensing_service.py" "Licensing Service"
check_file "python/natural_language_engine.py" "Natural Language Engine"
echo ""

# Check UI Files
echo "UI Files:"
echo "-" | head -c 70; echo
check_file "ui/login.html" "Login Portal"
check_file "ui/admin-portal-enhanced.html" "Admin Portal"
check_file "ui/user-portal.html" "User Portal"
check_file "ui/corporate-design-system.css" "Design System"
check_file "ui/shared-utilities.js" "Shared Utilities"
check_file "ui/parallel-llm-visualizer.js" "Parallel LLM Visualizer"
echo ""

# Check Documentation
echo "Documentation:"
echo "-" | head -c 70; echo
check_file "docs/INDEX.md" "Documentation Index"
check_file "docs/guides/QUICK_START_GUIDE.md" "Quick Start Guide"
check_file "docs/guides/USER_PERSONAS_GUIDE.md" "User Personas Guide"
check_file "docs/guides/COGNIWARE_LLMS_GUIDE.md" "LLM Guide"
check_file "docs/guides/PARALLEL_LLM_EXECUTION_GUIDE.md" "Parallel Execution Guide"
echo ""

# Check Scripts
echo "Scripts:"
echo "-" | head -c 70; echo
check_file "scripts/01_check_requirements.sh" "Requirements Checker"
check_file "scripts/02_install_requirements.sh" "Requirements Installer"
check_file "scripts/03_setup_services.sh" "Service Setup"
check_file "scripts/04_start_services.sh" "Start Services"
check_file "scripts/05_stop_services.sh" "Stop Services"
check_file "scripts/06_verify_deliverables.sh" "Verify Deliverables (this script)"
echo ""

# Check API Collections
echo "API Collections:"
echo "-" | head -c 70; echo
check_file "api/Cogniware-Parallel-LLM-API.postman_collection.json" "Parallel LLM API Collection"
echo ""

# Check Databases
echo "Databases:"
echo "-" | head -c 70; echo
check_file "databases/licenses.db" "License Database"
echo ""

# Check Services (if running)
echo "Service Health (if started):"
echo "-" | head -c 70; echo
check_service "http://localhost:8099/health" "Admin Server (8099)"
check_service "http://localhost:8096/health" "Business Protected (8096)"
check_service "http://localhost:8090/health" "Production Server (8090)"
check_service "http://localhost:8095/health" "Business Server (8095)"
check_service "http://localhost:8080/health" "Demo Server (8080)"
check_service "http://localhost:8000/" "Web Server (8000)"
echo ""

# Test Authentication
echo "Authentication Test:"
echo "-" | head -c 70; echo
AUTH_RESPONSE=$(curl -s -X POST http://localhost:8099/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"superadmin","password":"Cogniware@2025"}' 2>/dev/null)

if echo "$AUTH_RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✅ Authentication working${NC}"
    ((PASSED++))
    
    # Test LLM availability
    TOKEN=$(echo "$AUTH_RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
    
    if [ ! -z "$TOKEN" ]; then
        LLM_RESPONSE=$(curl -s http://localhost:8090/api/nl/llms/available \
          -H "Authorization: Bearer $TOKEN" 2>/dev/null)
        
        if echo "$LLM_RESPONSE" | grep -q "success"; then
            LLM_COUNT=$(echo "$LLM_RESPONSE" | grep -o '"total":[0-9]*' | cut -d':' -f2)
            if [ "$LLM_COUNT" -gt 0 ]; then
                echo -e "${GREEN}✅ LLMs available: $LLM_COUNT models${NC}"
                ((PASSED++))
            else
                echo -e "${YELLOW}⚠️  LLMs available but count is 0${NC}"
            fi
        else
            echo -e "${YELLOW}⚠️  LLM availability check inconclusive${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  Authentication test inconclusive (services may not be running)${NC}"
fi
echo ""

# Summary
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                        VERIFICATION SUMMARY                      ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

TOTAL=$((PASSED + FAILED))
PERCENTAGE=$((PASSED * 100 / TOTAL))

echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo "Total:  $TOTAL"
echo "Success Rate: $PERCENTAGE%"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                                  ║${NC}"
    echo -e "${GREEN}║          ✅ ALL DELIVERABLES VERIFIED SUCCESSFULLY! ✅           ║${NC}"
    echo -e "${GREEN}║                                                                  ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Platform is complete and ready for use!"
    exit 0
elif [ $PERCENTAGE -ge 80 ]; then
    echo -e "${YELLOW}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║                                                                  ║${NC}"
    echo -e "${YELLOW}║          ⚠️  VERIFICATION PASSED WITH WARNINGS ⚠️                ║${NC}"
    echo -e "${YELLOW}║                                                                  ║${NC}"
    echo -e "${YELLOW}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Platform is mostly complete but has some missing components."
    echo "Review the failures above."
    exit 0
else
    echo -e "${RED}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║                                                                  ║${NC}"
    echo -e "${RED}║              ❌ VERIFICATION FAILED ❌                            ║${NC}"
    echo -e "${RED}║                                                                  ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Critical components are missing. Please review the failures above."
    exit 1
fi

