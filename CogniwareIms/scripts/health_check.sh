#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

###############################################################################
# Health Check Script - OPEA IMS
# Comprehensive system health verification
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}🏥 OPEA IMS - Comprehensive Health Check${NC}"
echo -e "${BLUE}=====================================================================${NC}"
echo ""

# Function to check service health
check_service() {
    local name=$1
    local url=$2
    local timeout=${3:-5}

    if curl -sf --max-time $timeout "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name${NC} - Healthy"
        return 0
    else
        echo -e "${RED}❌ $name${NC} - Unhealthy or not responding"
        return 1
    fi
}

# Function to check Docker service
check_docker_service() {
    local service=$1
    local status=$(docker-compose ps -q $service 2>/dev/null)

    if [ -n "$status" ]; then
        local health=$(docker inspect --format='{{.State.Health.Status}}' $(docker-compose ps -q $service) 2>/dev/null || echo "unknown")
        if [ "$health" = "healthy" ] || [ "$health" = "unknown" ]; then
            echo -e "${GREEN}✅ $service${NC} - Running"
            return 0
        else
            echo -e "${YELLOW}⚠️  $service${NC} - Running but health: $health"
            return 1
        fi
    else
        echo -e "${RED}❌ $service${NC} - Not running"
        return 1
    fi
}

# Track health status
healthy_count=0
total_checks=0

echo "📦 Checking Docker Services..."
echo "================================"

services=("frontend" "backend" "postgres" "redis" "embedding-service" "llm-service" "retrieval-service" "opea-gateway")

for service in "${services[@]}"; do
    ((total_checks++))
    if check_docker_service $service; then
        ((healthy_count++))
    fi
done

echo ""
echo "🌐 Checking HTTP Endpoints..."
echo "================================"

endpoints=(
    "Frontend:http://localhost:3000"
    "Backend API:http://localhost:8000/api/health"
    "API Docs:http://localhost:8000/docs"
    "Embedding Service:http://localhost:6000/health:15"
    "LLM Service:http://localhost:9000/health:15"
)

for endpoint in "${endpoints[@]}"; do
    IFS=':' read -ra PARTS <<< "$endpoint"
    name="${PARTS[0]}"
    url="${PARTS[1]}:${PARTS[2]}"
    timeout="${PARTS[3]:-5}"

    ((total_checks++))
    if check_service "$name" "$url" "$timeout"; then
        ((healthy_count++))
    fi
done

echo ""
echo "💾 Checking Data Stores..."
echo "================================"

# PostgreSQL
((total_checks++))
if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL${NC} - Ready"
    ((healthy_count++))

    # Check database exists
    if docker-compose exec -T postgres psql -U postgres -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw opea_ims; then
        echo -e "${GREEN}   ↳ Database 'opea_ims' exists${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Database 'opea_ims' not found${NC}"
    fi
else
    echo -e "${RED}❌ PostgreSQL${NC} - Not ready"
fi

# Redis
((total_checks++))
if docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
    echo -e "${GREEN}✅ Redis${NC} - Ready"
    ((healthy_count++))

    # Check Redis memory
    redis_mem=$(docker-compose exec -T redis redis-cli INFO memory 2>/dev/null | grep used_memory_human | cut -d: -f2 | tr -d '\r')
    echo -e "${GREEN}   ↳ Memory used: $redis_mem${NC}"
else
    echo -e "${RED}❌ Redis${NC} - Not ready"
fi

echo ""
echo "📊 System Resources..."
echo "================================"

# Docker stats (quick snapshot)
echo "Container Resource Usage:"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" | head -n 10

echo ""
echo "🔍 Knowledge Base Status..."
echo "================================"

((total_checks++))
if kb_stats=$(curl -sf http://localhost:8000/api/knowledge/stats 2>/dev/null); then
    total_docs=$(echo $kb_stats | grep -o '"total_documents":[0-9]*' | cut -d: -f2)
    echo -e "${GREEN}✅ Knowledge Base${NC} - Accessible"
    echo -e "${GREEN}   ↳ Total Documents: ${total_docs:-0}${NC}"
    ((healthy_count++))
else
    echo -e "${YELLOW}⚠️  Knowledge Base${NC} - API not responding"
fi

echo ""
echo "🔐 Security Checks..."
echo "================================"

# Check if using default secrets
if docker-compose exec -T backend printenv JWT_SECRET_KEY 2>/dev/null | grep -q "CHANGE_THIS"; then
    echo -e "${RED}❌ Security Warning: Using default JWT secret!${NC}"
    echo -e "${RED}   ↳ Update JWT_SECRET_KEY in .env${NC}"
else
    echo -e "${GREEN}✅ JWT Secret${NC} - Custom key configured"
fi

if docker-compose exec -T postgres printenv POSTGRES_PASSWORD 2>/dev/null | grep -q "^postgres$"; then
    echo -e "${RED}❌ Security Warning: Using default PostgreSQL password!${NC}"
    echo -e "${RED}   ↳ Update POSTGRES_PASSWORD in .env${NC}"
else
    echo -e "${GREEN}✅ PostgreSQL Password${NC} - Custom password configured"
fi

echo ""
echo -e "${BLUE}=====================================================================${NC}"
echo -e "${BLUE}📈 Health Check Summary${NC}"
echo -e "${BLUE}=====================================================================${NC}"

health_percentage=$((healthy_count * 100 / total_checks))

echo ""
echo -e "Healthy Services: ${GREEN}$healthy_count${NC}/$total_checks"
echo -e "Health Score: ${GREEN}$health_percentage%${NC}"
echo ""

if [ $health_percentage -ge 90 ]; then
    echo -e "${GREEN}✅ System Status: EXCELLENT${NC}"
    echo -e "${GREEN}   All critical services are operational${NC}"
    exit_code=0
elif [ $health_percentage -ge 70 ]; then
    echo -e "${YELLOW}⚠️  System Status: DEGRADED${NC}"
    echo -e "${YELLOW}   Some services may not be fully operational${NC}"
    echo -e "${YELLOW}   Review failed checks above${NC}"
    exit_code=1
else
    echo -e "${RED}❌ System Status: CRITICAL${NC}"
    echo -e "${RED}   Multiple services are not operational${NC}"
    echo -e "${RED}   Immediate attention required${NC}"
    exit_code=2
fi

echo ""
echo -e "${BLUE}📝 Quick Actions${NC}"
echo "================================"
echo "View logs:           docker-compose logs -f"
echo "Restart service:     docker-compose restart <service>"
echo "Full restart:        docker-compose restart"
echo "View details:        docker-compose ps"
echo ""

exit $exit_code
