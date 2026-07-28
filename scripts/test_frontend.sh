#!/bin/bash
# AIQuantification Frontend Test Script (Linux/Mac)

set -e

echo "========================================"
echo "AIQuantification Frontend Test Script"
echo "========================================"
echo ""

# Step 1: Start Backend
echo "[Step 1] Starting Backend Service..."
cd "$(dirname "$0")"
python -m uvicorn main:app --host 127.0.0.1 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
sleep 3

# Step 2: Check Backend Health
echo "[Step 2] Checking Backend Health..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✓ Backend is running!"
else
    echo "✗ Backend failed to start"
    cat backend.log
    exit 1
fi
echo ""

# Step 3: Install Frontend Dependencies
echo "[Step 3] Installing Frontend Dependencies..."
cd web
if [ ! -d "node_modules" ]; then
    echo "Installing npm packages..."
    npm install
else
    echo "✓ Dependencies already installed"
fi
echo ""

# Step 4: Start Frontend
echo "[Step 4] Starting Frontend Dev Server..."
echo "Opening http://localhost:5173 in your browser..."
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:5173 &
elif command -v open > /dev/null; then
    open http://localhost:5173 &
fi

npm run dev

# Cleanup on exit
trap "kill $BACKEND_PID 2>/dev/null" EXIT
