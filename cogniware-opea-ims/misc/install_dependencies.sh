#!/bin/bash

# MSmartCompute Engine Dependencies Installer for Linux
# This script installs all required dependencies for building MSmartCompute Engine

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Print with color
print_message() {
    echo -e "${GREEN}[MSmartCompute Dependencies]${NC} $1"
}

print_error() {
    echo -e "${RED}[Error]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[Warning]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run as root"
    exit 1
fi

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    print_error "Cannot detect Linux distribution"
    exit 1
fi

print_message "Detected OS: $OS $VER"

# Function to install dependencies for Ubuntu/Debian
install_ubuntu_deps() {
    print_message "Installing dependencies for Ubuntu/Debian..."
    
    # Update package list
    sudo apt update
    
    # Install build essentials
    sudo apt install -y build-essential cmake git wget curl
    
    # Install CUDA dependencies
    sudo apt install -y nvidia-cuda-toolkit nvidia-cuda-dev
    
    # Install Python dependencies
    sudo apt install -y python3 python3-pip python3-dev python3-venv
    
    # Install C++ dependencies
    sudo apt install -y libjsoncpp-dev libspdlog-dev libcurl4-openssl-dev zlib1g-dev libuuid1 uuid-dev
    
    # Install OpenMP
    sudo apt install -y libomp-dev
    
    # Install GTest
    sudo apt install -y libgtest-dev
    
    # Install pkg-config
    sudo apt install -y pkg-config
}

# Function to install dependencies for CentOS/RHEL/Fedora
install_centos_deps() {
    print_message "Installing dependencies for CentOS/RHEL/Fedora..."
    
    # Install EPEL repository for CentOS/RHEL
    if [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
        sudo yum install -y epel-release
    fi
    
    # Install build tools
    sudo yum groupinstall -y "Development Tools"
    sudo yum install -y cmake git wget curl
    
    # Install CUDA (if available)
    if command -v nvidia-smi &> /dev/null; then
        print_message "NVIDIA GPU detected, installing CUDA..."
        # Note: CUDA installation might need to be done manually
        print_warning "Please install CUDA manually from NVIDIA website"
    fi
    
    # Install Python
    sudo yum install -y python3 python3-pip python3-devel
    
    # Install C++ dependencies
    sudo yum install -y jsoncpp-devel spdlog-devel libcurl-devel zlib-devel libuuid-devel
    
    # Install OpenMP
    sudo yum install -y libomp-devel
    
    # Install GTest
    sudo yum install -y gtest-devel
    
    # Install pkg-config
    sudo yum install -y pkgconfig
}

# Function to install dependencies for Arch Linux
install_arch_deps() {
    print_message "Installing dependencies for Arch Linux..."
    
    # Update package list
    sudo pacman -Syu
    
    # Install build tools
    sudo pacman -S --noconfirm base-devel cmake git wget curl
    
    # Install CUDA
    sudo pacman -S --noconfirm cuda cudnn
    
    # Install Python
    sudo pacman -S --noconfirm python python-pip
    
    # Install C++ dependencies
    sudo pacman -S --noconfirm jsoncpp spdlog curl zlib util-linux
    
    # Install OpenMP
    sudo pacman -S --noconfirm openmp
    
    # Install GTest
    sudo pacman -S --noconfirm gtest
    
    # Install pkg-config
    sudo pacman -S --noconfirm pkgconf
}

# Install dependencies based on distribution
case $OS in
    *"Ubuntu"*|*"Debian"*)
        install_ubuntu_deps
        ;;
    *"CentOS"*|*"Red Hat"*|*"Fedora"*)
        install_centos_deps
        ;;
    *"Arch"*)
        install_arch_deps
        ;;
    *)
        print_error "Unsupported Linux distribution: $OS"
        print_message "Please install dependencies manually:"
        print_message "- build-essential/cmake/git"
        print_message "- CUDA toolkit"
        print_message "- Python 3.8+"
        print_message "- jsoncpp, spdlog, curl, zlib, uuid libraries"
        print_message "- OpenMP, GTest"
        exit 1
        ;;
esac

# Install Python dependencies
print_message "Installing Python dependencies..."
python3 -m pip install --user --upgrade pip
python3 -m pip install --user numpy torch pybind11 streamlit pandas plotly requests pydantic python-dateutil

# Install pybind11 system-wide for development
sudo python3 -m pip install pybind11

# Set up environment variables
print_message "Setting up environment variables..."
cat >> ~/.bashrc << EOL

# MSmartCompute Engine environment variables
export CUDA_HOME=/usr/local/cuda
export PATH=\$CUDA_HOME/bin:\$PATH
export LD_LIBRARY_PATH=\$CUDA_HOME/lib64:\$LD_LIBRARY_PATH
EOL

# Source the updated bashrc
source ~/.bashrc

print_message "Dependencies installation completed!"
print_message "Please restart your terminal or run 'source ~/.bashrc' to apply environment changes."
print_message "You can now run the setup.sh script to build MSmartCompute Engine." 