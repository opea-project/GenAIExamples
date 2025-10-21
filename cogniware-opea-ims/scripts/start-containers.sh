#!/bin/bash

# MSmartCompute Platform Container Startup Script
# This script builds and starts all containers for the MSmartCompute platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to check if Docker Compose is available
check_docker_compose() {
    if ! command -v docker-compose > /dev/null 2>&1; then
        print_error "Docker Compose is not installed. Please install Docker Compose and try again."
        exit 1
    fi
    print_success "Docker Compose is available"
}

# Function to check NVIDIA Docker runtime
check_nvidia_docker() {
    if ! docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi > /dev/null 2>&1; then
        print_warning "NVIDIA Docker runtime is not available. GPU acceleration will not work."
        print_warning "Please install nvidia-docker2 and restart Docker."
    else
        print_success "NVIDIA Docker runtime is available"
    fi
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p models logs cache temp
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/datasources
    mkdir -p nginx/ssl
    
    print_success "Directories created"
}

# Function to create sample model file
create_sample_model() {
    if [ ! -f "models/test-model.bin" ]; then
        print_status "Creating sample model file..."
        # Create a dummy model file for testing
        dd if=/dev/zero of=models/test-model.bin bs=1M count=100 2>/dev/null || true
        print_success "Sample model file created"
    fi
}

# Function to build and start containers
start_containers() {
    print_status "Building and starting MSmartCompute platform containers..."
    
    # Build and start all services
    docker-compose up -d --build
    
    print_success "Containers started successfully"
}

# Function to wait for services to be ready
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    # Wait for MSmartCompute platform
    print_status "Waiting for MSmartCompute platform..."
    timeout=120
    counter=0
    while [ $counter -lt $timeout ]; do
        if curl -f http://localhost:8080/health > /dev/null 2>&1; then
            print_success "MSmartCompute platform is ready"
            break
        fi
        sleep 2
        counter=$((counter + 2))
        echo -n "."
    done
    
    if [ $counter -eq $timeout ]; then
        print_warning "MSmartCompute platform took longer than expected to start"
    fi
    
    # Wait for PostgreSQL
    print_status "Waiting for PostgreSQL..."
    timeout=60
    counter=0
    while [ $counter -lt $timeout ]; do
        if docker exec msmartcompute-postgres pg_isready -U msmartcompute > /dev/null 2>&1; then
            print_success "PostgreSQL is ready"
            break
        fi
        sleep 2
        counter=$((counter + 2))
        echo -n "."
    done
    
    if [ $counter -eq $timeout ]; then
        print_warning "PostgreSQL took longer than expected to start"
    fi
    
    # Wait for Redis
    print_status "Waiting for Redis..."
    timeout=30
    counter=0
    while [ $counter -lt $timeout ]; do
        if docker exec msmartcompute-redis redis-cli ping > /dev/null 2>&1; then
            print_success "Redis is ready"
            break
        fi
        sleep 2
        counter=$((counter + 2))
        echo -n "."
    done
    
    if [ $counter -eq $timeout ]; then
        print_warning "Redis took longer than expected to start"
    fi
    
    echo ""
}

# Function to display service status
show_status() {
    print_status "Container status:"
    docker-compose ps
    
    echo ""
    print_status "Service endpoints:"
    echo "  MSmartCompute Platform API: http://localhost:8080"
    echo "  Nginx (Reverse Proxy):      http://localhost:80"
    echo "  Grafana (Monitoring):       http://localhost:3000"
    echo "  Prometheus (Metrics):       http://localhost:9090"
    echo "  PostgreSQL:                 localhost:5432"
    echo "  Redis:                      localhost:6379"
    
    echo ""
    print_status "Default credentials:"
    echo "  Grafana: admin / admin123"
    echo "  PostgreSQL: msmartcompute / msmartcompute123"
    echo "  API Key: test-api-key-123"
}

# Function to run health checks
run_health_checks() {
    print_status "Running health checks..."
    
    # Check MSmartCompute platform
    if curl -f http://localhost:8080/health > /dev/null 2>&1; then
        print_success "MSmartCompute platform health check passed"
    else
        print_error "MSmartCompute platform health check failed"
    fi
    
    # Check API endpoints
    if curl -f http://localhost:8080/api/v1/models > /dev/null 2>&1; then
        print_success "API endpoints are accessible"
    else
        print_warning "API endpoints may not be ready yet"
    fi
    
    # Check Grafana
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        print_success "Grafana is accessible"
    else
        print_warning "Grafana may not be ready yet"
    fi
    
    # Check Prometheus
    if curl -f http://localhost:9090 > /dev/null 2>&1; then
        print_success "Prometheus is accessible"
    else
        print_warning "Prometheus may not be ready yet"
    fi
}

# Function to show logs
show_logs() {
    print_status "Recent logs from MSSmartCompute platform:"
    docker-compose logs --tail=20 msmartcompute
}

# Main execution
main() {
    echo "=========================================="
    echo "MSmartCompute Platform Container Startup"
    echo "=========================================="
    echo ""
    
    # Check prerequisites
    check_docker
    check_docker_compose
    check_nvidia_docker
    
    # Create directories and files
    create_directories
    create_sample_model
    
    # Start containers
    start_containers
    
    # Wait for services
    wait_for_services
    
    # Show status
    show_status
    
    # Run health checks
    run_health_checks
    
    # Show logs
    show_logs
    
    echo ""
    print_success "MSmartCompute platform is now running!"
    echo ""
    print_status "To stop the platform, run: docker-compose down"
    print_status "To view logs, run: docker-compose logs -f"
    print_status "To restart, run: docker-compose restart"
}

# Handle command line arguments
case "${1:-}" in
    "stop")
        print_status "Stopping MSmartCompute platform..."
        docker-compose down
        print_success "Platform stopped"
        ;;
    "restart")
        print_status "Restarting MSSmartCompute platform..."
        docker-compose restart
        print_success "Platform restarted"
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "status")
        docker-compose ps
        ;;
    "health")
        run_health_checks
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  (no args)  Start the platform"
        echo "  stop       Stop the platform"
        echo "  restart    Restart the platform"
        echo "  logs       Show logs"
        echo "  status     Show container status"
        echo "  health     Run health checks"
        echo "  help       Show this help"
        ;;
    *)
        main
        ;;
esac 