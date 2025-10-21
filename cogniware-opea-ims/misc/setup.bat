@echo off
setlocal enabledelayedexpansion

:: Colors for output
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "NC=[0m"

:: Print with color
:print_message
echo %GREEN%[MSmartCompute Setup]%NC% %~1
goto :eof

:print_error
echo %RED%[Error]%NC% %~1
goto :eof

:print_warning
echo %YELLOW%[Warning]%NC% %~1
goto :eof

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    call :print_error "Please do not run as administrator"
    exit /b 1
)

:: Check CUDA
where nvidia-smi >nul 2>&1
if %errorLevel% neq 0 (
    call :print_error "NVIDIA GPU not detected. MSmartCompute requires CUDA support."
    exit /b 1
)

:: Get CUDA version
for /f "tokens=*" %%a in ('nvidia-smi ^| findstr "CUDA Version"') do set CUDA_VERSION=%%a
call :print_message "Detected CUDA version: %CUDA_VERSION%"

:: Check CMake
where cmake >nul 2>&1
if %errorLevel% neq 0 (
    call :print_error "CMake is not installed. Please install CMake 3.15 or higher."
    exit /b 1
)

:: Check Visual Studio
if not exist "%ProgramFiles(x86)%\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvars64.bat" (
    call :print_error "Visual Studio 2019 or higher is required."
    exit /b 1
)

:: Create build directory
call :print_message "Creating build directory..."
if not exist build mkdir build
cd build

:: Configure CMake
call :print_message "Configuring CMake..."
cmake .. -G "Visual Studio 16 2019" -A x64 ^
    -DCMAKE_BUILD_TYPE=Release ^
    -DCMAKE_TOOLCHAIN_FILE="C:\vcpkg\scripts\buildsystems\vcpkg.cmake" ^
    -DCUDA_TOOLKIT_ROOT_DIR="%CUDA_PATH%" ^
    -DCMAKE_CUDA_COMPILER="%CUDA_PATH%\bin\nvcc.exe"

:: Build
call :print_message "Building MSmartCompute..."
cmake --build . --config Release

:: Install
call :print_message "Installing MSmartCompute..."
cmake --install . --config Release

:: Create Python virtual environment
call :print_message "Setting up Python environment..."
cd ..
python -m venv venv
call venv\Scripts\activate.bat

:: Install Python dependencies
call :print_message "Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

:: Create necessary directories
call :print_message "Creating directories..."
if not exist models mkdir models
if not exist logs mkdir logs
if not exist data mkdir data

:: Set up environment variables
call :print_message "Setting up environment variables..."
(
echo CUDA_VISIBLE_DEVICES=0
echo MSMARTCOMPUTE_MODEL_PATH=models
echo MSMARTCOMPUTE_LOG_PATH=logs
echo MSMARTCOMPUTE_DATA_PATH=data
) > .env

:: Download default models
call :print_message "Downloading default models..."
python scripts\download_models.py

call :print_message "Setup completed successfully!"
call :print_message "You can now use MSmartCompute in your Python code:"
call :print_message "from msmartcompute import MSmartCompute"
call :print_message "session = MSmartCompute(model_path='models/your_model')"

endlocal 