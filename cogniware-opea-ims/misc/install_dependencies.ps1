# MSmartCompute Engine Dependencies Installer for Windows
# This script installs all required dependencies for building MSmartCompute Engine

param(
    [switch]$SkipCUDA,
    [switch]$SkipVisualStudio,
    [string]$CUDAVersion = "11.8"
)

# Colors for output
$Green = "`e[92m"
$Red = "`e[91m"
$Yellow = "`e[93m"
$Reset = "`e[0m"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = $Green)
    Write-Host "$Color$Message$Reset"
}

function Write-ErrorOutput {
    param([string]$Message)
    Write-Host "$Red[Error]$Reset $Message"
}

function Write-WarningOutput {
    param([string]$Message)
    Write-Host "$Yellow[Warning]$Reset $Message"
}

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-ErrorOutput "Please run this script as Administrator"
    exit 1
}

Write-ColorOutput "Installing MSmartCompute Engine dependencies..."

# Install Chocolatey if not present
if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-ColorOutput "Installing Chocolatey..."
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    refreshenv
}

# Install Visual Studio Build Tools
if (-not $SkipVisualStudio) {
    Write-ColorOutput "Installing Visual Studio Build Tools..."
    choco install visualstudio2019buildtools --package-parameters "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended" -y
    choco install visualstudio2019-workload-vctools -y
}

# Install CMake
Write-ColorOutput "Installing CMake..."
choco install cmake -y

# Install Python
Write-ColorOutput "Installing Python..."
choco install python -y

# Install Git
Write-ColorOutput "Installing Git..."
choco install git -y

# Install vcpkg for C++ dependencies
Write-ColorOutput "Installing vcpkg..."
if (-not (Test-Path "C:\vcpkg")) {
    git clone https://github.com/Microsoft/vcpkg.git C:\vcpkg
    C:\vcpkg\bootstrap-vcpkg.bat
    C:\vcpkg\vcpkg integrate install
}

# Install C++ dependencies via vcpkg
Write-ColorOutput "Installing C++ dependencies..."
C:\vcpkg\vcpkg install jsoncpp:x64-windows
C:\vcpkg\vcpkg install spdlog:x64-windows
C:\vcpkg\vcpkg install curl:x64-windows
C:\vcpkg\vcpkg install zlib:x64-windows
C:\vcpkg\vcpkg install gtest:x64-windows
C:\vcpkg\vcpkg install pybind11:x64-windows

# Install CUDA if not skipped
if (-not $SkipCUDA) {
    Write-ColorOutput "Installing CUDA Toolkit..."
    $cudaUrl = "https://developer.download.nvidia.com/compute/cuda/$CUDAVersion/Prod/local_installers/cuda_${CUDAVersion}_windows.exe"
    $cudaInstaller = "$env:TEMP\cuda_installer.exe"
    
    try {
        Invoke-WebRequest -Uri $cudaUrl -OutFile $cudaInstaller
        Start-Process -FilePath $cudaInstaller -ArgumentList "/s" -Wait
        Remove-Item $cudaInstaller -Force
    }
    catch {
        Write-WarningOutput "Failed to download CUDA installer. Please install CUDA manually from NVIDIA website."
    }
}

# Install Python dependencies
Write-ColorOutput "Installing Python dependencies..."
python -m pip install --upgrade pip
python -m pip install numpy torch pybind11 streamlit pandas plotly requests pydantic python-dateutil

# Set environment variables
Write-ColorOutput "Setting environment variables..."
$envVars = @{
    "CUDA_PATH" = "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v$CUDAVersion"
    "VCPKG_ROOT" = "C:\vcpkg"
    "CMAKE_TOOLCHAIN_FILE" = "C:\vcpkg\scripts\buildsystems\vcpkg.cmake"
}

foreach ($var in $envVars.GetEnumerator()) {
    [Environment]::SetEnvironmentVariable($var.Key, $var.Value, [EnvironmentVariableTarget]::Machine)
    Write-ColorOutput "Set $($var.Key) = $($var.Value)"
}

Write-ColorOutput "Dependencies installation completed!"
Write-ColorOutput "Please restart your terminal to apply environment variable changes."
Write-ColorOutput "You can now run the setup.bat script to build MSmartCompute Engine."