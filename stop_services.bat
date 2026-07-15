@echo off
echo Stopping AIQuantification Services...
echo.

echo [1] Stopping Backend (Port 8000)...
FOR /F "tokens=5" %%P IN ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') DO (
    echo Killing process %%P
    taskkill /F /PID %%P
)

echo.
echo [2] Stopping Frontend (Port 5173)...
FOR /F "tokens=5" %%P IN ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') DO (
    echo Killing process %%P
    taskkill /F /PID %%P
)

echo.
echo [3] Verifying services stopped...
timeout /t 2 /nobreak > nul

curl -s http://localhost:8000/health > nul 2>&1
if %errorlevel% neq 0 (
    echo [OK] Backend stopped
) else (
    echo [WARNING] Backend still running
)

curl -s http://localhost:5173 > nul 2>&1
if %errorlevel% neq 0 (
    echo [OK] Frontend stopped
) else (
    echo [WARNING] Frontend still running
)

echo.
echo ========================================
echo All services stopped!
echo ========================================
pause
