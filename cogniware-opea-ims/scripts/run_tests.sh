#!/bin/bash

# Exit on error
set -e

# Check if build directory exists
if [ ! -d "build" ]; then
    echo "Build directory not found. Running build script first..."
    ./scripts/build.sh
fi

# Run tests
cd build
ctest --output-on-failure

echo "Tests completed successfully!" 