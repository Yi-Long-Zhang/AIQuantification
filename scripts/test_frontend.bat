@echo off
echo ========================================
echo AIQuantification Frontend Test Script
echo ========================================
echo.

echo [Step 1] Starting Backend Service...
cd C:\code\PycharmProjects\AIQuantification
start /B python -m uvicorn main:app --host 127.0.0.1 --port 8000 > backend.log 2>&1
timeout /t 3 /nobreak > nul

echo [Step 2] Checking Backend Health...
curl -s http://localhost:8000/health
if %errorlevel% neq 0 (
    echo ERROR: Backend failed to start
    type backend.log
    exit /b 1
)
echo Backend is running!
echo.

echo [Step 3] Installing Frontend Dependencies...
cd web
if not exist node_modules (
    echo Installing npm packages...
    call npm install
    if %errorlevel% neq 0 (
        echo ERROR: npm install failed
        exit /b 1
    )
) else (
    echo Dependencies already installed
)
echo.

echo [Step 4] Starting Frontend Dev Server...
echo Opening http://localhost:5173 in your browser...
start http://localhost:5173
call npm run dev

pause
