#!/bin/bash

# Exit on error
set -e

# Create build directory if it doesn't exist
mkdir -p build
cd build

# Configure with CMake
cmake ..

# Build
cmake --build . --config Release

# Install (optional)
# cmake --install .

echo "Build completed successfully!" 