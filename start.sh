#!/bin/bash

# Learnora - Linux/Mac Startup Script
# =====================================

echo "=========================================="
echo "  🎓 Learnora - Starting Application"
echo "=========================================="

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python is installed
echo ""
echo "Checking dependencies..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    echo "Install with: sudo apt install python3 python3-pip"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found${NC}"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    echo "Install with: sudo apt install nodejs npm"
    exit 1
fi
echo -e "${GREEN}✓ Node.js found${NC}"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed${NC}"
    echo "Install with: sudo apt install npm"
    exit 1
fi
echo -e "${GREEN}✓ npm found${NC}"

# Check if backend dependencies are installed
echo ""
echo "Checking backend dependencies..."
if [ ! -d "webapp/backend" ]; then
    echo -e "${RED}Error: webapp/backend directory not found${NC}"
    exit 1
fi

cd webapp/backend
if ! python3 -c "import flask" &> /dev/null; then
    echo -e "${YELLOW}Installing backend dependencies...${NC}"
    pip3 install -r requirements.txt
fi
echo -e "${GREEN}✓ Backend dependencies ready${NC}"

# Check if frontend dependencies are installed
echo ""
echo "Checking frontend dependencies..."
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
fi
echo -e "${GREEN}✓ Frontend dependencies ready${NC}"

cd ../..

# Create log directory if it doesn't exist
mkdir -p logs

# Start Backend
echo ""
echo "=========================================="
echo "Starting Backend (Flask on port 5000)..."
echo "=========================================="
cd webapp/backend
python3 app.py > ../../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}Backend started with PID: $BACKEND_PID${NC}"
cd ../..

# Wait for backend to start
echo ""
echo "Waiting for backend to initialize..."
sleep 3

# Check if backend is running
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}Error: Backend failed to start${NC}"
    echo "Check logs/backend.log for details"
    exit 1
fi

# Start Frontend
echo ""
echo "=========================================="
echo "Starting Frontend (React on port 3000)..."
echo "=========================================="
cd webapp/frontend

# Set environment variable to auto-open browser (optional)
export BROWSER=none

npm start > ../../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}Frontend started with PID: $FRONTEND_PID${NC}"
cd ../..

# Wait for frontend to start
echo ""
echo "Waiting for frontend to initialize..."
sleep 5

# Check if frontend is running
if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}✓ Frontend is running${NC}"
else
    echo -e "${RED}Warning: Frontend may have failed to start${NC}"
    echo "Check logs/frontend.log for details"
fi

# Final status
echo ""
echo "=========================================="
echo "  ✅ Learnora is now running!"
echo "=========================================="
echo ""
echo -e "🌐 ${GREEN}Backend:${NC}  http://localhost:5000"
echo -e "🌐 ${GREEN}Frontend:${NC} http://localhost:3000"
echo ""
echo -e "📊 ${YELLOW}Logs:${NC}"
echo "   - Backend:  logs/backend.log"
echo "   - Frontend: logs/frontend.log"
echo ""
echo -e "🛑 ${YELLOW}To stop Learnora:${NC}"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   or press Ctrl+C in this terminal"
echo ""
echo "=========================================="

# Save PIDs to file for easy cleanup
echo "$BACKEND_PID" > logs/backend.pid
echo "$FRONTEND_PID" > logs/frontend.pid

# Trap Ctrl+C to cleanup
cleanup() {
    echo ""
    echo ""
    echo "=========================================="
    echo "  Shutting down Learnora..."
    echo "=========================================="
    echo "Stopping backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null
    echo "Stopping frontend (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID 2>/dev/null
    echo "Cleanup complete!"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep script running and monitor processes
while true; do
    if ! ps -p $BACKEND_PID > /dev/null; then
        echo -e "${RED}Backend process died! Check logs/backend.log${NC}"
        kill $FRONTEND_PID 2>/dev/null
        exit 1
    fi
    if ! ps -p $FRONTEND_PID > /dev/null; then
        echo -e "${RED}Frontend process died! Check logs/frontend.log${NC}"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    sleep 5
done
