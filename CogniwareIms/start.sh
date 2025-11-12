#!/bin/bash
# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

Copyright (C) 2024 Intel Corporation
SPDX-License-Identifier: Apache-2.0

##############################################################################
# OPEA IMS - Production Deployment Script
# Cogniware AI-Powered Inventory Management System
##############################################################################

set -e  # Exit on error

echo "======================================================================"
echo "🚀 OPEA IMS - Cogniware Inventory Management System"
echo "======================================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  No .env file found. Creating from env.example...${NC}"
    cp env.example .env
    echo -e "${RED}⚠️  IMPORTANT: Edit .env and update JWT_SECRET_KEY and passwords!${NC}"
    echo -e "${RED}⚠️  Generate strong secret: openssl rand -hex 32${NC}"
    echo ""
    read -p "Press Enter after updating .env file to continue..."
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check system resources
echo "📊 Checking system resources..."
TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
if [ "$TOTAL_MEM" -lt 16 ]; then
    echo -e "${YELLOW}⚠️  Warning: System has ${TOTAL_MEM}GB RAM. Recommended: 16GB+${NC}"
fi

# Check disk space
DISK_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$DISK_SPACE" -lt 50 ]; then
    echo -e "${YELLOW}⚠️  Warning: Only ${DISK_SPACE}GB free disk space. Recommended: 50GB+${NC}"
fi

echo ""
echo "📦 Starting deployment..."
echo ""

# Pull latest images
echo "⬇️  Pulling Docker images..."
docker-compose pull || docker compose pull

# Build custom images
echo ""
echo "🔨 Building application images..."
docker-compose build || docker compose build

# Start services
echo ""
echo "🚀 Starting all services..."
docker-compose up -d || docker compose up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo ""
echo "🏥 Checking service health..."

check_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✅ $service is healthy${NC}"
            return 0
        fi
        echo -ne "  ⏳ $service (attempt $attempt/$max_attempts)...\r"
        sleep 2
        ((attempt++))
    done

    echo -e "  ${RED}❌ $service failed to start${NC}"
    return 1
}

# Check individual services
check_service "Frontend" "http://localhost:3000"
check_service "Backend API" "http://localhost:8000/api/health"
check_service "PostgreSQL" "http://localhost:5432" || echo -e "  ${YELLOW}⚠️  PostgreSQL (not HTTP accessible, check docker ps)${NC}"
check_service "Redis" "http://localhost:6379" || echo -e "  ${YELLOW}⚠️  Redis (not HTTP accessible, check docker ps)${NC}"

# OPEA services may take longer
echo ""
echo "⏳ Checking OPEA microservices (may take a few minutes)..."
sleep 20
check_service "Embedding Service" "http://localhost:6000/health" || echo -e "  ${YELLOW}⚠️  Embedding service starting (this is normal)${NC}"
check_service "LLM Service" "http://localhost:9000/health" || echo -e "  ${YELLOW}⚠️  LLM service starting (this is normal)${NC}"

echo ""
echo "======================================================================"
echo -e "${GREEN}✅ OPEA IMS Deployment Complete!${NC}"
echo "======================================================================"
echo ""
echo "📍 Access Points:"
echo "  🌐 Frontend:       http://localhost:3000"
echo "  📡 Backend API:    http://localhost:8000"
echo "  📚 API Docs:       http://localhost:8000/docs"
echo "  🔍 RedisInsight:   http://localhost:8001"
echo ""
echo "🔑 Default Credentials:"
echo "  Consumer:          consumer@company.com / password123"
echo "  Inventory Manager: inventory@company.com / password123"
echo "  Admin:             admin@company.com / password123"
echo ""
echo "⚠️  IMPORTANT: Change default passwords in production!"
echo ""
echo "📖 Next Steps:"
echo "  1. Initialize knowledge base:"
echo "     docker-compose exec backend python app/init_knowledge_base.py"
echo ""
echo "  2. View logs:"
echo "     docker-compose logs -f"
echo ""
echo "  3. Stop services:"
echo "     docker-compose down"
echo ""
echo "  4. Full reset (including data):"
echo "     docker-compose down -v"
echo ""
echo "======================================================================"
echo ""

# Ask if user wants to initialize knowledge base now
read -p "Would you like to initialize the knowledge base now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔄 Initializing knowledge base..."
    docker-compose exec -T backend python app/init_knowledge_base.py || docker compose exec -T backend python app/init_knowledge_base.py
    echo ""
    echo -e "${GREEN}✅ Knowledge base initialized!${NC}"
fi

echo ""
echo "🎉 System is ready! Open http://localhost:3000 in your browser."
echo ""
