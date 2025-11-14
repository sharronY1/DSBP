# DSBP Quick Start Script
# Usage: .\quick_start.ps1

Write-Host "=== DSBP Quick Start Script ===" -ForegroundColor Green
Write-Host ""

# Check Python
Write-Host "1. Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   ✓ Python installed: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Python not installed, please install Python 3.9+" -ForegroundColor Red
    exit 1
}

# Check .env file
Write-Host "2. Checking environment variables file..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "   Creating .env file..." -ForegroundColor Yellow
    Copy-Item "env.example" ".env"
    
    # Generate random JWT key
    $jwtKey = python -c "import secrets; print(secrets.token_urlsafe(32))" 2>&1
    $content = Get-Content ".env" -Raw
    $content = $content -replace 'your-secret-key-change-this-in-production', $jwtKey
    Set-Content ".env" -Value $content -NoNewline
    
    Write-Host "   ✓ .env file created" -ForegroundColor Green
    Write-Host "   ⚠ Please edit .env file and set correct DATABASE_URL" -ForegroundColor Yellow
} else {
    Write-Host "   ✓ .env file exists" -ForegroundColor Green
}

# Check virtual environment
Write-Host "3. Checking Python virtual environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    Write-Host "   Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    Write-Host "   ✓ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "   ✓ Virtual environment exists" -ForegroundColor Green
}

# Activate virtual environment and install dependencies
Write-Host "4. Installing Python dependencies..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
pip install --upgrade pip
pip install -r requirements.txt
Write-Host "   ✓ Dependencies installed" -ForegroundColor Green

# Check database
Write-Host "5. Database setup..." -ForegroundColor Yellow
Write-Host "   Please make sure PostgreSQL is installed and running" -ForegroundColor Yellow
Write-Host "   If you haven't created the database yet, execute these SQL commands:" -ForegroundColor Yellow
Write-Host "   CREATE DATABASE dsbp_db;" -ForegroundColor Cyan
Write-Host "   CREATE USER dsbp_user WITH PASSWORD 'dsbp_password';" -ForegroundColor Cyan
Write-Host "   GRANT ALL PRIVILEGES ON DATABASE dsbp_db TO dsbp_user;" -ForegroundColor Cyan
Write-Host ""

# Ask if initialize database
$initDb = Read-Host "Initialize database now? (y/n)"
if ($initDb -eq "y" -or $initDb -eq "Y") {
    Write-Host "   Initializing database..." -ForegroundColor Yellow
    python -m backend.db.init_db
    Write-Host "   ✓ Database initialized" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Run backend server:" -ForegroundColor Yellow
Write-Host "  python run.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend will run at http://localhost:8000" -ForegroundColor Green
Write-Host "API Documentation: http://localhost:8000/api/docs" -ForegroundColor Green

