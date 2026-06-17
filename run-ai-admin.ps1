# AI Admin Dashboard Launcher
# Tkinter-based native application

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  AI Admin Dashboard - Tkinter" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if AI Engine is running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
    Write-Host "AI Engine connected" -ForegroundColor Green
} catch {
    Write-Host "Warning: AI Engine not reachable at http://localhost:8000" -ForegroundColor Yellow
    Write-Host "Make sure Docker services are running: docker-compose up -d" -ForegroundColor Gray
}

# Install dependencies if needed
if (-not (Test-Path "services\ai-admin-tkinter\requirements.txt")) {
    Write-Host "Error: Tkinter app not found" -ForegroundColor Red
    exit 1
}

Write-Host "`nInstalling dependencies..." -ForegroundColor Gray
pip install -q -r services\ai-admin-tkinter\requirements.txt

Write-Host "`nLaunching AI Admin Dashboard..." -ForegroundColor Green
Write-Host ""

# Run the application
python services\ai-admin-tkinter\main.py
