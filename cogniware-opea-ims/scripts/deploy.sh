#!/bin/bash
################################################################################
# Cogniware Core - Automated Deployment Script
# Company: Cogniware Incorporated
# Description: Complete automated deployment with GPU detection, driver setup,
#              dependency installation, and systemd service configuration
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/cogniware-core"
SERVICE_USER="cogniware"
VENV_DIR="$INSTALL_DIR/venv"
LOG_DIR="/var/log/cogniware"
DATA_DIR="/var/lib/cogniware"

# Function to print colored output
print_info() {
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

print_header() {
    echo ""
    echo "════════════════════════════════════════════════════════════════"
    echo -e "${GREEN}$1${NC}"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
}

# Function to check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Function to detect OS
detect_os() {
    print_header "Detecting Operating System"
    
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        OS_VERSION=$VERSION_ID
        print_info "OS: $NAME $VERSION"
    else
        print_error "Cannot detect OS"
        exit 1
    fi
    
    # Check if Ubuntu/Debian based
    if [[ "$OS" != "ubuntu" ]] && [[ "$OS" != "debian" ]]; then
        print_warning "This script is optimized for Ubuntu/Debian. Proceeding anyway..."
    fi
}

# Function to detect GPU
detect_gpu() {
    print_header "Detecting GPU Hardware"
    
    GPU_DETECTED=false
    GPU_TYPE=""
    GPU_MODEL=""
    
    # Check for NVIDIA GPU
    if lspci | grep -i nvidia > /dev/null 2>&1; then
        GPU_DETECTED=true
        GPU_TYPE="nvidia"
        GPU_MODEL=$(lspci | grep -i nvidia | grep -i vga | head -1)
        print_success "NVIDIA GPU detected: $GPU_MODEL"
    fi
    
    # Check for AMD GPU
    if lspci | grep -i amd | grep -i vga > /dev/null 2>&1; then
        if [ "$GPU_DETECTED" = false ]; then
            GPU_DETECTED=true
            GPU_TYPE="amd"
        fi
        GPU_MODEL=$(lspci | grep -i amd | grep -i vga | head -1)
        print_success "AMD GPU detected: $GPU_MODEL"
    fi
    
    # Check for Intel GPU
    if lspci | grep -i intel | grep -i vga > /dev/null 2>&1; then
        if [ "$GPU_DETECTED" = false ]; then
            GPU_DETECTED=true
            GPU_TYPE="intel"
        fi
        GPU_MODEL=$(lspci | grep -i intel | grep -i vga | head -1)
        print_info "Intel GPU detected: $GPU_MODEL"
    fi
    
    if [ "$GPU_DETECTED" = false ]; then
        print_warning "No dedicated GPU detected. Using CPU-only mode."
        GPU_TYPE="none"
    fi
}

# Function to install base dependencies
install_base_dependencies() {
    print_header "Installing Base Dependencies"
    
    print_info "Updating package lists..."
    apt-get update -qq
    
    print_info "Installing essential packages..."
    apt-get install -y -qq \
        build-essential \
        cmake \
        git \
        wget \
        curl \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        pkg-config \
        software-properties-common \
        lsb-release \
        ca-certificates \
        apt-transport-https \
        gnupg
    
    print_success "Base dependencies installed"
}

# Function to install NVIDIA drivers and CUDA
install_nvidia_stack() {
    print_header "Installing NVIDIA Drivers and CUDA"
    
    # Check if drivers already installed
    if nvidia-smi > /dev/null 2>&1; then
        print_info "NVIDIA drivers already installed"
        nvidia-smi
        return
    fi
    
    print_info "Installing NVIDIA drivers..."
    
    # Add NVIDIA repository
    wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb -O /tmp/cuda-keyring.deb 2>/dev/null || true
    if [ -f /tmp/cuda-keyring.deb ]; then
        dpkg -i /tmp/cuda-keyring.deb
        apt-get update -qq
    fi
    
    # Install NVIDIA driver
    apt-get install -y -qq nvidia-driver-535 || apt-get install -y -qq nvidia-driver-525 || print_warning "Could not install NVIDIA driver via package manager"
    
    # Install CUDA toolkit
    apt-get install -y -qq cuda-toolkit-12-2 || print_warning "Could not install CUDA toolkit"
    
    # Install cuDNN
    apt-get install -y -qq libcudnn8 libcudnn8-dev || print_warning "Could not install cuDNN"
    
    print_success "NVIDIA stack installation complete"
    print_warning "A reboot may be required for drivers to take effect"
}

# Function to install AMD ROCm
install_amd_rocm() {
    print_header "Installing AMD ROCm"
    
    print_info "Adding AMD ROCm repository..."
    wget -q -O - https://repo.radeon.com/rocm/rocm.gpg.key | apt-key add - || true
    echo 'deb [arch=amd64] https://repo.radeon.com/rocm/apt/debian/ ubuntu main' | tee /etc/apt/sources.list.d/rocm.list
    
    apt-get update -qq
    
    print_info "Installing ROCm..."
    apt-get install -y -qq rocm-hip-sdk rocm-opencl-sdk || print_warning "Could not install ROCm"
    
    print_success "AMD ROCm installation complete"
}

# Function to create system user
create_system_user() {
    print_header "Creating System User"
    
    if id "$SERVICE_USER" &>/dev/null; then
        print_info "User $SERVICE_USER already exists"
    else
        useradd -r -s /bin/bash -d "$INSTALL_DIR" -m "$SERVICE_USER"
        print_success "User $SERVICE_USER created"
    fi
}

# Function to create directories
create_directories() {
    print_header "Creating Directory Structure"
    
    # Create installation directory
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$DATA_DIR/databases"
    mkdir -p "$DATA_DIR/projects"
    mkdir -p "$DATA_DIR/documents"
    mkdir -p "$DATA_DIR/models"
    
    print_success "Directories created"
}

# Function to copy application files
copy_application() {
    print_header "Copying Application Files"
    
    CURRENT_DIR=$(pwd)
    
    print_info "Copying files to $INSTALL_DIR..."
    
    # Copy Python files
    cp -r "$CURRENT_DIR/python" "$INSTALL_DIR/" || true
    
    # Copy UI files
    print_info "Copying UI files..."
    mkdir -p "$INSTALL_DIR/ui"
    cp -r "$CURRENT_DIR/ui/"* "$INSTALL_DIR/ui/" 2>/dev/null || print_warning "No UI files found"
    
    # Copy configuration
    cp "$CURRENT_DIR/config.json" "$INSTALL_DIR/" 2>/dev/null || echo '{}' > "$INSTALL_DIR/config.json"
    
    # Copy requirements
    cp "$CURRENT_DIR/requirements.txt" "$INSTALL_DIR/" 2>/dev/null || true
    
    # Copy documentation
    mkdir -p "$INSTALL_DIR/docs"
    cp -r "$CURRENT_DIR/docs/"* "$INSTALL_DIR/docs/" 2>/dev/null || true
    cp -r "$CURRENT_DIR/api" "$INSTALL_DIR/" 2>/dev/null || true
    
    # Copy key documentation files
    cp "$CURRENT_DIR/USER_PERSONAS_GUIDE.md" "$INSTALL_DIR/" 2>/dev/null || true
    cp "$CURRENT_DIR/README.md" "$INSTALL_DIR/" 2>/dev/null || true
    cp "$CURRENT_DIR/QUICK_START_GUIDE.md" "$INSTALL_DIR/" 2>/dev/null || true
    cp "$CURRENT_DIR/DEPLOYMENT_GUIDE.md" "$INSTALL_DIR/" 2>/dev/null || true
    
    # Copy databases
    print_info "Setting up databases..."
    mkdir -p "$DATA_DIR/databases"
    cp -r "$CURRENT_DIR/databases/"* "$DATA_DIR/databases/" 2>/dev/null || print_warning "No databases found"
    
    print_success "Application files copied"
}

# Function to create Python virtual environment
create_virtualenv() {
    print_header "Creating Python Virtual Environment"
    
    print_info "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    
    print_info "Upgrading pip..."
    "$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel -q
    
    print_success "Virtual environment created"
}

# Function to install Python dependencies
install_python_dependencies() {
    print_header "Installing Python Dependencies"
    
    print_info "Installing core dependencies..."
    "$VENV_DIR/bin/pip" install -q \
        flask \
        flask-cors \
        requests \
        psutil \
        pynvml \
        nvidia-ml-py \
        sqlite3 2>/dev/null || true
    
    # Install requirements.txt if exists
    if [ -f "$INSTALL_DIR/requirements.txt" ]; then
        print_info "Installing from requirements.txt..."
        "$VENV_DIR/bin/pip" install -q -r "$INSTALL_DIR/requirements.txt" || true
    fi
    
    # GPU-specific dependencies
    if [ "$GPU_TYPE" = "nvidia" ]; then
        print_info "Installing NVIDIA-specific packages..."
        "$VENV_DIR/bin/pip" install -q nvidia-ml-py3 pycuda 2>/dev/null || true
    fi
    
    if [ "$GPU_TYPE" = "amd" ]; then
        print_info "Installing AMD-specific packages..."
        # AMD-specific packages would go here
        true
    fi
    
    print_success "Python dependencies installed"
}

# Function to set permissions
set_permissions() {
    print_header "Setting Permissions"
    
    chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$LOG_DIR"
    chown -R "$SERVICE_USER:$SERVICE_USER" "$DATA_DIR"
    
    chmod 755 "$INSTALL_DIR"
    chmod 755 "$LOG_DIR"
    chmod 755 "$DATA_DIR"
    
    # Make Python files executable
    find "$INSTALL_DIR/python" -name "*.py" -exec chmod +x {} \; 2>/dev/null || true
    
    print_success "Permissions set"
}

# Function to create systemd service files
create_systemd_services() {
    print_header "Creating Systemd Services"
    
    # Admin Server Service
    cat > /etc/systemd/system/cogniware-admin.service << EOF
[Unit]
Description=Cogniware Core - Admin Server
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$VENV_DIR/bin/python3 $INSTALL_DIR/python/api_server_admin.py
Restart=always
RestartSec=10
StandardOutput=append:$LOG_DIR/admin.log
StandardError=append:$LOG_DIR/admin-error.log

[Install]
WantedBy=multi-user.target
EOF
    
    # Business Protected Server Service
    cat > /etc/systemd/system/cogniware-business-protected.service << EOF
[Unit]
Description=Cogniware Core - Business Protected Server
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$VENV_DIR/bin/python3 $INSTALL_DIR/python/api_server_business_protected.py
Restart=always
RestartSec=10
StandardOutput=append:$LOG_DIR/business-protected.log
StandardError=append:$LOG_DIR/business-protected-error.log

[Install]
WantedBy=multi-user.target
EOF
    
    # Demo Server Service
    cat > /etc/systemd/system/cogniware-demo.service << EOF
[Unit]
Description=Cogniware Core - Demo Server
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$VENV_DIR/bin/python3 $INSTALL_DIR/python/api_server.py
Restart=always
RestartSec=10
StandardOutput=append:$LOG_DIR/demo.log
StandardError=append:$LOG_DIR/demo-error.log

[Install]
WantedBy=multi-user.target
EOF
    
    # Production Server Service
    cat > /etc/systemd/system/cogniware-production.service << EOF
[Unit]
Description=Cogniware Core - Production Server
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$VENV_DIR/bin/python3 $INSTALL_DIR/python/api_server_production.py
Restart=always
RestartSec=10
StandardOutput=append:$LOG_DIR/production.log
StandardError=append:$LOG_DIR/production-error.log

[Install]
WantedBy=multi-user.target
EOF
    
    # Business Server Service
    cat > /etc/systemd/system/cogniware-business.service << EOF
[Unit]
Description=Cogniware Core - Business Server
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$VENV_DIR/bin/python3 $INSTALL_DIR/python/api_server_business.py
Restart=always
RestartSec=10
StandardOutput=append:$LOG_DIR/business.log
StandardError=append:$LOG_DIR/business-error.log

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    print_success "Systemd services created (5 servers)"
}

# Function to create configuration file
create_configuration() {
    print_header "Creating Configuration"
    
    cat > "$INSTALL_DIR/config.json" << EOF
{
  "installation": {
    "install_dir": "$INSTALL_DIR",
    "data_dir": "$DATA_DIR",
    "log_dir": "$LOG_DIR",
    "user": "$SERVICE_USER"
  },
  "hardware": {
    "gpu_type": "$GPU_TYPE",
    "gpu_model": "$GPU_MODEL"
  },
  "servers": {
    "admin": {
      "host": "0.0.0.0",
      "port": 8099,
      "enabled": true,
      "description": "Super admin portal (protected)"
    },
    "business_protected": {
      "host": "0.0.0.0",
      "port": 8096,
      "enabled": true,
      "description": "Business operations (protected)"
    },
    "demo": {
      "host": "0.0.0.0",
      "port": 8080,
      "enabled": true,
      "description": "Architecture showcase"
    },
    "production": {
      "host": "0.0.0.0",
      "port": 8090,
      "enabled": true,
      "description": "Production with GPU"
    },
    "business": {
      "host": "0.0.0.0",
      "port": 8095,
      "enabled": true,
      "description": "Legacy business features"
    }
  },
  "logging": {
    "level": "INFO",
    "directory": "$LOG_DIR"
  }
}
EOF
    
    chown "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR/config.json"
    print_success "Configuration created"
}

# Function to create management script
create_management_script() {
    print_header "Creating Management Script"
    
    cat > /usr/local/bin/cogniware << 'EOF'
#!/bin/bash
# Cogniware Core Management Script

SERVICES=("cogniware-admin" "cogniware-business-protected" "cogniware-demo" "cogniware-production" "cogniware-business")

case "$1" in
    start)
        echo "Starting Cogniware Core services..."
        for service in "${SERVICES[@]}"; do
            sudo systemctl start "$service"
            echo "  - $service started"
        done
        ;;
    stop)
        echo "Stopping Cogniware Core services..."
        for service in "${SERVICES[@]}"; do
            sudo systemctl stop "$service"
            echo "  - $service stopped"
        done
        ;;
    restart)
        echo "Restarting Cogniware Core services..."
        for service in "${SERVICES[@]}"; do
            sudo systemctl restart "$service"
            echo "  - $service restarted"
        done
        ;;
    status)
        echo "Cogniware Core service status:"
        echo ""
        for service in "${SERVICES[@]}"; do
            sudo systemctl status "$service" --no-pager | head -3
            echo ""
        done
        ;;
    logs)
        SERVICE=${2:-cogniware-demo}
        echo "Tailing logs for $SERVICE..."
        sudo journalctl -u "$SERVICE" -f
        ;;
    enable)
        echo "Enabling Cogniware Core services (start on boot)..."
        for service in "${SERVICES[@]}"; do
            sudo systemctl enable "$service"
            echo "  - $service enabled"
        done
        ;;
    disable)
        echo "Disabling Cogniware Core services..."
        for service in "${SERVICES[@]}"; do
            sudo systemctl disable "$service"
            echo "  - $service disabled"
        done
        ;;
    test)
        echo "Testing Cogniware Core endpoints..."
        echo ""
        echo "Demo Server (8080):"
        curl -s http://localhost:8080/health 2>/dev/null || echo "  Not responding"
        echo ""
        echo "Production Server (8090):"
        curl -s http://localhost:8090/health 2>/dev/null || echo "  Not responding"
        echo ""
        echo "Business Server (8095):"
        curl -s http://localhost:8095/health 2>/dev/null || echo "  Not responding"
        ;;
    *)
        echo "Cogniware Core Management Tool"
        echo ""
        echo "Usage: cogniware {start|stop|restart|status|logs|enable|disable|test}"
        echo ""
        echo "Commands:"
        echo "  start    - Start all services"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  status   - Show service status"
        echo "  logs     - Tail service logs (default: demo)"
        echo "  enable   - Enable services on boot"
        echo "  disable  - Disable services on boot"
        echo "  test     - Test all endpoints"
        echo ""
        echo "Examples:"
        echo "  cogniware start"
        echo "  cogniware status"
        echo "  cogniware logs cogniware-production"
        echo "  cogniware test"
        ;;
esac
EOF
    
    chmod +x /usr/local/bin/cogniware
    print_success "Management script created: cogniware"
}

# Function to configure firewall
configure_firewall() {
    print_header "Configuring Firewall"
    
    if command -v ufw &> /dev/null; then
        print_info "Configuring UFW firewall..."
        ufw allow 8099/tcp comment "Cogniware Admin Server" || true
        ufw allow 8096/tcp comment "Cogniware Business Protected Server" || true
        ufw allow 8080/tcp comment "Cogniware Demo Server" || true
        ufw allow 8090/tcp comment "Cogniware Production Server" || true
        ufw allow 8095/tcp comment "Cogniware Business Server" || true
        print_success "Firewall rules added for all 5 servers"
    else
        print_warning "UFW not found, skipping firewall configuration"
    fi
}

# Function to start services
start_services() {
    print_header "Starting Services"
    
    # Enable services
    systemctl enable cogniware-admin.service
    systemctl enable cogniware-business-protected.service
    systemctl enable cogniware-demo.service
    systemctl enable cogniware-production.service
    systemctl enable cogniware-business.service
    
    # Start services
    systemctl start cogniware-admin.service
    systemctl start cogniware-business-protected.service
    systemctl start cogniware-demo.service
    systemctl start cogniware-production.service
    systemctl start cogniware-business.service
    
    sleep 5
    
    # Check status
    print_info "Checking service status..."
    systemctl is-active --quiet cogniware-admin.service && print_success "Admin server running" || print_warning "Admin server not running"
    systemctl is-active --quiet cogniware-business-protected.service && print_success "Business Protected server running" || print_warning "Business Protected server not running"
    systemctl is-active --quiet cogniware-demo.service && print_success "Demo server running" || print_warning "Demo server not running"
    systemctl is-active --quiet cogniware-production.service && print_success "Production server running" || print_warning "Production server not running"
    systemctl is-active --quiet cogniware-business.service && print_success "Business server running" || print_warning "Business server not running"
}

# Function to test endpoints
test_endpoints() {
    print_header "Testing Endpoints"
    
    sleep 5  # Give servers time to start
    
    print_info "Testing Admin Server (8099)..."
    if curl -s http://localhost:8099/health > /dev/null 2>&1; then
        print_success "Admin Server responding"
    else
        print_warning "Admin Server not responding"
    fi
    
    print_info "Testing Business Protected Server (8096)..."
    if curl -s http://localhost:8096/health > /dev/null 2>&1; then
        print_success "Business Protected Server responding"
    else
        print_warning "Business Protected Server not responding"
    fi
    
    print_info "Testing Demo Server (8080)..."
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        print_success "Demo Server responding"
    else
        print_warning "Demo Server not responding"
    fi
    
    print_info "Testing Production Server (8090)..."
    if curl -s http://localhost:8090/health > /dev/null 2>&1; then
        print_success "Production Server responding"
    else
        print_warning "Production Server not responding"
    fi
    
    print_info "Testing Business Server (8095)..."
    if curl -s http://localhost:8095/health > /dev/null 2>&1; then
        print_success "Business Server responding"
    else
        print_warning "Business Server not responding"
    fi
}

# Function to print final summary
print_summary() {
    print_header "Installation Complete!"
    
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}║          COGNIWARE CORE SUCCESSFULLY DEPLOYED!               ║${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Installation Details:"
    echo "  Installation Directory: $INSTALL_DIR"
    echo "  Data Directory: $DATA_DIR"
    echo "  Log Directory: $LOG_DIR"
    echo "  Service User: $SERVICE_USER"
    echo "  GPU Type: $GPU_TYPE"
    echo ""
    echo "Services:"
    echo "  Admin Server:      http://localhost:8099 (Protected)"
    echo "  Business Protected: http://localhost:8096 (Protected)"
    echo "  Demo Server:       http://localhost:8080"
    echo "  Production Server: http://localhost:8090 (Real GPU)"
    echo "  Business Server:   http://localhost:8095 (Legacy)"
    echo ""
    echo "Web Interfaces:"
    echo "  Login Portal:      http://localhost:8099/ui/login.html"
    echo "  Super Admin:       http://localhost:8099/ui/admin-portal-enhanced.html"
    echo "  Admin Dashboard:   http://localhost:8099/ui/admin-dashboard.html"
    echo "  User Portal:       http://localhost:8099/ui/user-portal.html"
    echo ""
    echo "Default Credentials:"
    echo "  Super Admin Username: superadmin"
    echo "  Super Admin Password: Cogniware@2025"
    echo "  ⚠️  CHANGE PASSWORD IMMEDIATELY!"
    echo ""
    echo "Management:"
    echo "  cogniware start    - Start all services"
    echo "  cogniware stop     - Stop all services"
    echo "  cogniware status   - Check status"
    echo "  cogniware logs     - View logs"
    echo "  cogniware test     - Test endpoints"
    echo ""
    echo "Systemd Services:"
    echo "  systemctl status cogniware-admin"
    echo "  systemctl status cogniware-business-protected"
    echo "  systemctl status cogniware-demo"
    echo "  systemctl status cogniware-production"
    echo "  systemctl status cogniware-business"
    echo ""
    echo "Logs:"
    echo "  $LOG_DIR/admin.log"
    echo "  $LOG_DIR/business-protected.log"
    echo "  $LOG_DIR/demo.log"
    echo "  $LOG_DIR/production.log"
    echo "  $LOG_DIR/business.log"
    echo ""
    echo "Documentation:"
    echo "  $INSTALL_DIR/USER_PERSONAS_GUIDE.md"
    echo "  $INSTALL_DIR/QUICK_START_GUIDE.md"
    echo "  $INSTALL_DIR/README.md"
    echo ""
    
    if [ "$GPU_TYPE" = "nvidia" ]; then
        echo -e "${YELLOW}Note: If NVIDIA drivers were just installed, a reboot is recommended.${NC}"
        echo ""
    fi
    
    echo -e "${GREEN}Ready for production use!${NC}"
    echo ""
}

################################################################################
# Main Execution
################################################################################

main() {
    clear
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                  ║"
    echo "║              COGNIWARE CORE AUTOMATED DEPLOYMENT                 ║"
    echo "║                                                                  ║"
    echo "║                  Cogniware Incorporated                          ║"
    echo "║                                                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Pre-flight checks
    check_root
    detect_os
    detect_gpu
    
    # Installation steps
    install_base_dependencies
    
    # GPU-specific installation
    if [ "$GPU_TYPE" = "nvidia" ]; then
        install_nvidia_stack
    elif [ "$GPU_TYPE" = "amd" ]; then
        install_amd_rocm
    fi
    
    # Application setup
    create_system_user
    create_directories
    copy_application
    create_virtualenv
    install_python_dependencies
    set_permissions
    
    # Service configuration
    create_systemd_services
    create_configuration
    create_management_script
    configure_firewall
    
    # Start and test
    start_services
    test_endpoints
    
    # Final summary
    print_summary
}

# Run main function
main "$@"

