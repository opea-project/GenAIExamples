#!/bin/bash
################################################################################
# Cogniware Core - Uninstall Script
# Company: Cogniware Incorporated
# Description: Complete removal of Cogniware Core installation
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

INSTALL_DIR="/opt/cogniware-core"
SERVICE_USER="cogniware"
LOG_DIR="/var/log/cogniware"
DATA_DIR="/var/lib/cogniware"

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

# Check root
if [[ $EUID -ne 0 ]]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║          COGNIWARE CORE UNINSTALLATION                           ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Confirmation
read -p "Are you sure you want to uninstall Cogniware Core? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

# Backup data
read -p "Do you want to backup data before uninstalling? (Y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    BACKUP_DIR="/tmp/cogniware-backup-$(date +%Y%m%d-%H%M%S)"
    print_info "Creating backup at $BACKUP_DIR..."
    mkdir -p "$BACKUP_DIR"
    cp -r "$DATA_DIR" "$BACKUP_DIR/" 2>/dev/null || true
    cp -r "$LOG_DIR" "$BACKUP_DIR/" 2>/dev/null || true
    cp "$INSTALL_DIR/config.json" "$BACKUP_DIR/" 2>/dev/null || true
    print_success "Backup created at $BACKUP_DIR"
fi

# Stop services
print_info "Stopping services..."
systemctl stop cogniware-demo.service 2>/dev/null || true
systemctl stop cogniware-production.service 2>/dev/null || true
systemctl stop cogniware-business.service 2>/dev/null || true
print_success "Services stopped"

# Disable services
print_info "Disabling services..."
systemctl disable cogniware-demo.service 2>/dev/null || true
systemctl disable cogniware-production.service 2>/dev/null || true
systemctl disable cogniware-business.service 2>/dev/null || true
print_success "Services disabled"

# Remove service files
print_info "Removing systemd service files..."
rm -f /etc/systemd/system/cogniware-demo.service
rm -f /etc/systemd/system/cogniware-production.service
rm -f /etc/systemd/system/cogniware-business.service
systemctl daemon-reload
print_success "Service files removed"

# Remove management script
print_info "Removing management script..."
rm -f /usr/local/bin/cogniware
print_success "Management script removed"

# Remove installation directory
print_info "Removing installation directory..."
rm -rf "$INSTALL_DIR"
print_success "Installation directory removed"

# Remove log directory
print_info "Removing log directory..."
rm -rf "$LOG_DIR"
print_success "Log directory removed"

# Ask about data directory
read -p "Remove data directory $DATA_DIR? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$DATA_DIR"
    print_success "Data directory removed"
else
    print_info "Data directory preserved at $DATA_DIR"
fi

# Ask about user
read -p "Remove service user $SERVICE_USER? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    userdel -r "$SERVICE_USER" 2>/dev/null || userdel "$SERVICE_USER" 2>/dev/null || true
    print_success "Service user removed"
else
    print_info "Service user preserved"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║          COGNIWARE CORE UNINSTALLED SUCCESSFULLY                 ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

if [ -d "$BACKUP_DIR" ]; then
    echo "Backup saved at: $BACKUP_DIR"
    echo ""
fi

print_success "Uninstallation complete!"

