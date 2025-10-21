@echo off
setlocal enabledelayedexpansion

REM MSSmartCompute Platform Container Startup Script for Windows
REM This script builds and starts all containers for the MSSmartCompute platform

echo ==========================================
echo MSSmartCompute Platform Container Startup
echo ==========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH.
    echo Please install Docker Desktop for Windows from: https://www.docker.com/products/docker-desktop
    echo After installation, restart your computer and try again.
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [SUCCESS] Docker is running

REM Check if Docker Compose is available
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose is not available. Please ensure Docker Desktop is properly installed.
    pause
    exit /b 1
)

echo [SUCCESS] Docker Compose is available

REM Create necessary directories
echo [INFO] Creating necessary directories...
if not exist "models" mkdir models
if not exist "logs" mkdir logs
if not exist "cache" mkdir cache
if not exist "temp" mkdir temp
if not exist "monitoring\grafana\dashboards" mkdir monitoring\grafana\dashboards
if not exist "monitoring\grafana\datasources" mkdir monitoring\grafana\datasources
if not exist "nginx\ssl" mkdir nginx\ssl

echo [SUCCESS] Directories created

REM Create sample model file
if not exist "models\test-model.bin" (
    echo [INFO] Creating sample model file...
    fsutil file createnew models\test-model.bin 104857600 >nul 2>&1
    echo [SUCCESS] Sample model file created
)

REM Build and start containers
echo [INFO] Building and starting MSSmartCompute platform containers...
docker-compose up -d --build

if %errorlevel% neq 0 (
    echo [ERROR] Failed to start containers. Check the error messages above.
    pause
    exit /b 1
)

echo [SUCCESS] Containers started successfully

REM Wait for services to be ready
echo [INFO] Waiting for services to be ready...

REM Wait for MSSmartCompute platform
echo [INFO] Waiting for MSSmartCompute platform...
set /a timeout=120
set /a counter=0
:wait_platform
if %counter% geq %timeout% (
    echo [WARNING] MSSmartCompute platform took longer than expected to start
    goto :show_status
)
curl -f http://localhost:8080/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] MSSmartCompute platform is ready
    goto :show_status
)
timeout /t 2 /nobreak >nul
set /a counter+=2
echo -n .
goto :wait_platform

:show_status
echo.
echo [INFO] Container status:
docker-compose ps

echo.
echo [INFO] Service endpoints:
echo   MSSmartCompute Platform API: http://localhost:8080
echo   Nginx (Reverse Proxy):      http://localhost:80
echo   Grafana (Monitoring):       http://localhost:3000
echo   Prometheus (Metrics):       http://localhost:9090
echo   PostgreSQL:                 localhost:5432
echo   Redis:                      localhost:6379

echo.
echo [INFO] Default credentials:
echo   Grafana: admin / admin123
echo   PostgreSQL: msmartcompute / msmartcompute123
echo   API Key: test-api-key-123

echo.
echo [SUCCESS] MSSmartCompute platform is now running!
echo.
echo [INFO] To stop the platform, run: docker-compose down
echo [INFO] To view logs, run: docker-compose logs -f
echo [INFO] To restart, run: docker-compose restart
echo.
echo [INFO] To test the API, run: scripts\test-api.bat
echo.
pause 