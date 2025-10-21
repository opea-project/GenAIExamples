#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Print with color
print_message() {
    echo -e "${GREEN}[MSmartCompute Setup]${NC} $1"
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

# Check CUDA
if ! command -v nvidia-smi &> /dev/null; then
    print_error "NVIDIA GPU not detected. MSmartCompute requires CUDA support."
    exit 1
fi

# Get CUDA version
CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}')
print_message "Detected CUDA version: $CUDA_VERSION"

# Check CMake
if ! command -v cmake &> /dev/null; then
    print_error "CMake is not installed. Please install CMake 3.15 or higher."
    exit 1
fi

# Check C++ compiler
if ! command -v g++ &> /dev/null; then
    print_error "GCC/G++ is not installed. Please install GCC 9 or higher."
    exit 1
fi

# Create build directory
print_message "Creating build directory..."
mkdir -p build
cd build

# Configure CMake
print_message "Configuring CMake..."
cmake .. -DCMAKE_BUILD_TYPE=Release \
         -DCUDA_TOOLKIT_ROOT_DIR=/usr/local/cuda \
         -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc

# Build
print_message "Building MSmartCompute..."
make -j$(nproc)

# Install
print_message "Installing MSmartCompute..."
sudo make install

# Create Python virtual environment
print_message "Setting up Python environment..."
cd ..
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_message "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
print_message "Creating directories..."
mkdir -p models
mkdir -p logs
mkdir -p data

# Set up environment variables
print_message "Setting up environment variables..."
cat > .env << EOL
CUDA_VISIBLE_DEVICES=0
MSMARTCOMPUTE_MODEL_PATH=models
MSMARTCOMPUTE_LOG_PATH=logs
MSMARTCOMPUTE_DATA_PATH=data
EOL

# Download default models
print_message "Downloading default models..."
python3 scripts/download_models.py

print_message "Setup completed successfully!"
print_message "You can now use MSmartCompute in your Python code:"
print_message "from msmartcompute import MSmartCompute"
print_message "session = MSmartCompute(model_path='models/your_model')" 