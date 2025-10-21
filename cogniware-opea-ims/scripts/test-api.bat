@echo off
setlocal enabledelayedexpansion

REM MSSmartCompute Platform API Test Script for Windows
REM This script tests all the API endpoints to ensure they're working correctly

REM Configuration
set BASE_URL=http://localhost:8080
set API_KEY=test-api-key-123

echo ==========================================
echo MSSmartCompute Platform API Test Suite
echo ==========================================
echo.

REM Wait for platform to be ready
echo [INFO] Waiting for MSSmartCompute platform to be ready...
set /a timeout=60
set /a counter=0
:wait_platform
if %counter% geq %timeout% (
    echo [ERROR] Platform did not become ready within %timeout% seconds
    pause
    exit /b 1
)
curl -f "%BASE_URL%/health" >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Platform is ready
    goto :run_tests
)
timeout /t 2 /nobreak >nul
set /a counter+=2
echo -n .
goto :wait_platform

:run_tests
echo.
echo [INFO] Starting comprehensive API tests...
echo.

REM Test health endpoint
echo [INFO] Testing health endpoint...
curl -s -w "%%{http_code}" -o temp_response.json "%BASE_URL%/health" > temp_status.txt
set /p status=<temp_status.txt
if "%status%"=="200" (
    echo [SUCCESS] GET /health - Status: %status%
) else (
    echo [ERROR] GET /health - Expected: 200, Got: %status%
)
del temp_response.json temp_status.txt >nul 2>&1

REM Test model management
echo.
echo [INFO] Testing model management endpoints...
curl -s -w "%%{http_code}" -o temp_response.json "%BASE_URL%/api/v1/models" > temp_status.txt
set /p status=<temp_status.txt
if "%status%"=="200" (
    echo [SUCCESS] GET /api/v1/models - Status: %status%
) else (
    echo [ERROR] GET /api/v1/models - Expected: 200, Got: %status%
)
del temp_response.json temp_status.txt >nul 2>&1

REM Test session management
echo.
echo [INFO] Testing session management endpoints...
curl -s -w "%%{http_code}" -o temp_response.json -H "Content-Type: application/json" -H "X-API-Key: %API_KEY%" -d "{\"user_id\": \"test-user-123\", \"model_id\": \"test-model\"}" "%BASE_URL%/api/v1/sessions" > temp_status.txt
set /p status=<temp_status.txt
if "%status%"=="200" (
    echo [SUCCESS] POST /api/v1/sessions - Status: %status%
) else (
    echo [ERROR] POST /api/v1/sessions - Expected: 200, Got: %status%
)
del temp_response.json temp_status.txt >nul 2>&1

REM Test inference
echo.
echo [INFO] Testing inference endpoints...
curl -s -w "%%{http_code}" -o temp_response.json -H "Content-Type: application/json" -H "X-API-Key: %API_KEY%" -d "{\"model_id\": \"test-model\", \"batch_size\": 1, \"sequence_length\": 128, \"data_type\": \"float32\", \"input_data\": [0.1, 0.2, 0.3]}" "%BASE_URL%/api/v1/inference" > temp_status.txt
set /p status=<temp_status.txt
if "%status%"=="200" (
    echo [SUCCESS] POST /api/v1/inference - Status: %status%
) else (
    echo [ERROR] POST /api/v1/inference - Expected: 200, Got: %status%
)
del temp_response.json temp_status.txt >nul 2>&1

REM Test performance metrics
echo.
echo [INFO] Testing performance metrics endpoints...
curl -s -w "%%{http_code}" -o temp_response.json "%BASE_URL%/api/v1/metrics" > temp_status.txt
set /p status=<temp_status.txt
if "%status%"=="200" (
    echo [SUCCESS] GET /api/v1/metrics - Status: %status%
) else (
    echo [ERROR] GET /api/v1/metrics - Expected: 200, Got: %status%
)
del temp_response.json temp_status.txt >nul 2>&1

REM Test resource management
echo.
echo [INFO] Testing resource management endpoints...
curl -s -w "%%{http_code}" -o temp_response.json "%BASE_URL%/api/v1/resources" > temp_status.txt
set /p status=<temp_status.txt
if "%status%"=="200" (
    echo [SUCCESS] GET /api/v1/resources - Status: %status%
) else (
    echo [ERROR] GET /api/v1/resources - Expected: 200, Got: %status%
)
del temp_response.json temp_status.txt >nul 2>&1

REM Test error handling
echo.
echo [INFO] Testing error handling...
curl -s -w "%%{http_code}" -o temp_response.json "%BASE_URL%/api/v1/models/invalid-model" > temp_status.txt
set /p status=<temp_status.txt
if "%status%"=="404" (
    echo [SUCCESS] GET /api/v1/models/invalid-model - Status: %status% (Expected 404)
) else (
    echo [ERROR] GET /api/v1/models/invalid-model - Expected: 404, Got: %status%
)
del temp_response.json temp_status.txt >nul 2>&1

echo.
echo ==========================================
echo [INFO] Test Results Summary:
echo [SUCCESS] Basic API functionality tests completed
echo ==========================================
echo.
echo [INFO] To view detailed logs, run: docker-compose logs -f msmartcompute
echo [INFO] To access the web interface, visit: http://localhost:8080
echo [INFO] To access Grafana monitoring, visit: http://localhost:3000
echo.
pause 