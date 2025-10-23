# Adaptive Learning Platform - Startup Script
# Run this script to start both backend and frontend

Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "Adaptive Learning Platform - Startup Script" -ForegroundColor Green
Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""

# Get the script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $scriptPath "backend"
$frontendPath = Join-Path $scriptPath "frontend"

# Check if Python is installed
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Yellow
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonVersion = python --version
    Write-Host "  ✓ $pythonVersion found" -ForegroundColor Green
} else {
    Write-Host "  ✗ Python not found! Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Check if Node.js is installed
Write-Host "[2/6] Checking Node.js installation..." -ForegroundColor Yellow
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVersion = node --version
    Write-Host "  ✓ Node.js $nodeVersion found" -ForegroundColor Green
} else {
    Write-Host "  ✗ Node.js not found! Please install Node.js 14+" -ForegroundColor Red
    exit 1
}

# Install backend dependencies
Write-Host "[3/6] Installing backend dependencies..." -ForegroundColor Yellow
Set-Location $backendPath
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt -q
    Write-Host "  ✓ Backend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  ✗ requirements.txt not found!" -ForegroundColor Red
    exit 1
}

# Install frontend dependencies (if node_modules doesn't exist)
Write-Host "[4/6] Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location $frontendPath
if (-not (Test-Path "node_modules")) {
    npm install --silent
    Write-Host "  ✓ Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  ✓ Frontend dependencies already installed" -ForegroundColor Green
}

# Start backend in background
Write-Host "[5/6] Starting Flask backend..." -ForegroundColor Yellow
Set-Location $backendPath
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python app.py" -WindowStyle Normal
Write-Host "  ✓ Backend starting at http://localhost:5000" -ForegroundColor Green
Start-Sleep -Seconds 3

# Start frontend in background
Write-Host "[6/6] Starting React frontend..." -ForegroundColor Yellow
Set-Location $frontendPath
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm start" -WindowStyle Normal
Write-Host "  ✓ Frontend starting at http://localhost:3000" -ForegroundColor Green

Write-Host ""
Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 70) -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend API:  " -NoNewline; Write-Host "http://localhost:5000" -ForegroundColor Cyan
Write-Host "Frontend App: " -NoNewline; Write-Host "http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to open the application in your browser..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "To stop the servers, close the PowerShell windows or press Ctrl+C" -ForegroundColor Yellow
Write-Host ""
