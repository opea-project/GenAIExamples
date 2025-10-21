# MSmartCompute Engine Build Guide

This guide explains how to build the MSmartCompute Engine on different platforms.

## Prerequisites

### System Requirements
- **CPU**: x86_64 processor with AVX2 support
- **RAM**: Minimum 8GB, recommended 16GB+
- **GPU**: NVIDIA GPU with CUDA support (RTX 20xx series or newer recommended)
- **Storage**: At least 10GB free space

### Software Requirements
- **CUDA**: Version 11.0 or higher
- **CMake**: Version 3.15 or higher
- **C++ Compiler**: GCC 9+ (Linux) or Visual Studio 2019+ (Windows)
- **Python**: Version 3.8 or higher
- **Git**: For cloning the repository

## Platform-Specific Setup

### Windows

#### 1. Install Dependencies
Run the PowerShell dependency installer as Administrator:

```powershell
# Run as Administrator
.\install_dependencies.ps1
```

This script will install:
- Visual Studio Build Tools 2019
- CUDA Toolkit 11.8
- CMake
- Python
- vcpkg and C++ dependencies
- Python packages

#### 2. Build the Engine
After installing dependencies, run the setup script:

```cmd
setup.bat
```

### Linux

#### 1. Install Dependencies
Run the Linux dependency installer:

```bash
chmod +x install_dependencies.sh
./install_dependencies.sh
```

This script supports:
- Ubuntu/Debian
- CentOS/RHEL/Fedora
- Arch Linux

#### 2. Build the Engine
After installing dependencies, run the setup script:

```bash
chmod +x setup.sh
./setup.sh
```

### macOS

#### 1. Install Dependencies
Install dependencies using Homebrew:

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install cmake python@3.9 git
brew install --cask cuda

# Install Python packages
pip3 install numpy torch pybind11 streamlit pandas plotly requests pydantic python-dateutil
```

#### 2. Build the Engine
```bash
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

## Manual Build Process

If the automated scripts don't work, you can build manually:

### 1. Clone and Prepare
```bash
git clone <repository-url>
cd cogniware_engine_cpp
```

### 2. Install Dependencies Manually

#### Windows (with vcpkg)
```cmd
# Install vcpkg
git clone https://github.com/Microsoft/vcpkg.git C:\vcpkg
C:\vcpkg\bootstrap-vcpkg.bat
C:\vcpkg\vcpkg integrate install

# Install C++ dependencies
C:\vcpkg\vcpkg install jsoncpp:x64-windows
C:\vcpkg\vcpkg install spdlog:x64-windows
C:\vcpkg\vcpkg install curl:x64-windows
C:\vcpkg\vcpkg install zlib:x64-windows
C:\vcpkg\vcpkg install gtest:x64-windows
C:\vcpkg\vcpkg install pybind11:x64-windows
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install -y build-essential cmake git python3 python3-pip
sudo apt install -y nvidia-cuda-toolkit nvidia-cuda-dev
sudo apt install -y libjsoncpp-dev libspdlog-dev libcurl4-openssl-dev zlib1g-dev libuuid1 uuid-dev
sudo apt install -y libomp-dev libgtest-dev pkg-config

pip3 install numpy torch pybind11 streamlit pandas plotly requests pydantic python-dateutil
```

### 3. Configure CMake

#### Windows
```cmd
mkdir build
cd build
cmake .. -G "Visual Studio 16 2019" -A x64 ^
    -DCMAKE_BUILD_TYPE=Release ^
    -DCMAKE_TOOLCHAIN_FILE="C:\vcpkg\scripts\buildsystems\vcpkg.cmake" ^
    -DCUDA_TOOLKIT_ROOT_DIR="%CUDA_PATH%" ^
    -DCMAKE_CUDA_COMPILER="%CUDA_PATH%\bin\nvcc.exe"
```

#### Linux
```bash
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release \
         -DCUDA_TOOLKIT_ROOT_DIR=/usr/local/cuda \
         -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc
```

### 4. Build
```bash
# Linux/macOS
make -j$(nproc)

# Windows
cmake --build . --config Release
```

### 5. Install
```bash
# Linux/macOS
sudo make install

# Windows
cmake --install . --config Release
```

## Troubleshooting

### Common Issues

#### 1. CUDA Not Found
**Error**: `Could not find CUDA`
**Solution**: 
- Ensure CUDA is installed and in PATH
- Set `CUDA_PATH` environment variable
- On Windows: `set CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8`
- On Linux: `export CUDA_HOME=/usr/local/cuda`

#### 2. Missing Dependencies
**Error**: `Could not find [library]`
**Solution**:
- Install missing libraries via package manager
- Use vcpkg on Windows
- Ensure pkg-config can find the libraries

#### 3. Python Issues
**Error**: `Could not find Python3`
**Solution**:
- Install Python development headers
- On Ubuntu: `sudo apt install python3-dev`
- On Windows: Install Python from python.org

#### 4. Compiler Issues
**Error**: `C++17 not supported`
**Solution**:
- Update to GCC 9+ or Visual Studio 2019+
- Set `CMAKE_CXX_STANDARD=17` in CMake

#### 5. Memory Issues
**Error**: `Out of memory during compilation`
**Solution**:
- Reduce parallel jobs: `make -j2` instead of `make -j$(nproc)`
- Close other applications
- Increase swap space

### Platform-Specific Issues

#### Windows
- **Visual Studio not found**: Install Visual Studio Build Tools 2019 or later
- **CUDA path issues**: Set `CUDA_PATH` environment variable
- **vcpkg issues**: Ensure vcpkg is properly installed and integrated

#### Linux
- **Permission denied**: Run dependency installation with sudo
- **Library not found**: Install development packages (e.g., `libjsoncpp-dev`)
- **CUDA not in PATH**: Add CUDA to PATH in `~/.bashrc`

#### macOS
- **CUDA not available**: Use CPU-only build or install CUDA manually
- **Homebrew issues**: Update Homebrew and try again

## Testing the Build

After successful build, test the installation:

```bash
# Run tests
cd build
ctest --output-on-failure

# Test Python interface
python3 -c "import cogniware_engine; print('Build successful!')"
```

## Next Steps

After building successfully:

1. **Download Models**: Run `python3 scripts/download_models.py`
2. **Configure Environment**: Set up environment variables
3. **Run Examples**: Check the `examples/` directory
4. **Integration**: Integrate with your application

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify all dependencies are installed correctly
3. Check the build logs for specific error messages
4. Open an issue on the project repository with:
   - Your platform and version
   - Complete error message
   - Build logs
   - Steps to reproduce 