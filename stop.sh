#!/bin/bash

# Learnora - Linux/Mac Stop Script
# ==================================

echo "=========================================="
echo "  🛑 Stopping Learnora"
echo "=========================================="

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if PID files exist
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping backend (PID: $BACKEND_PID)...${NC}"
        kill $BACKEND_PID
        echo -e "${GREEN}✓ Backend stopped${NC}"
    else
        echo -e "${YELLOW}Backend is not running${NC}"
    fi
    rm logs/backend.pid
else
    echo -e "${YELLOW}No backend PID file found${NC}"
    # Try to find and kill python app.py processes
    pkill -f "python3 app.py" && echo -e "${GREEN}✓ Killed python3 app.py processes${NC}"
fi

if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping frontend (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID
        echo -e "${GREEN}✓ Frontend stopped${NC}"
    else
        echo -e "${YELLOW}Frontend is not running${NC}"
    fi
    rm logs/frontend.pid
else
    echo -e "${YELLOW}No frontend PID file found${NC}"
    # Try to find and kill npm start processes
    pkill -f "npm start" && echo -e "${GREEN}✓ Killed npm start processes${NC}"
fi

# Also kill any react-scripts processes
pkill -f "react-scripts start" 2>/dev/null && echo -e "${GREEN}✓ Killed react-scripts processes${NC}"

# Also kill any node processes running on port 3000
lsof -ti:3000 | xargs kill -9 2>/dev/null && echo -e "${GREEN}✓ Killed processes on port 3000${NC}"

# Also kill any python processes running on port 5000
lsof -ti:5000 | xargs kill -9 2>/dev/null && echo -e "${GREEN}✓ Killed processes on port 5000${NC}"

echo ""
echo -e "${GREEN}=========================================="
echo "  ✅ Learnora stopped successfully"
echo "==========================================${NC}"
