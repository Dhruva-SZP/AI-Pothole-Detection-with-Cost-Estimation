Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  Launching AI Pothole Detection Platform in Production Mode" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$distPath = Join-Path $PSScriptRoot "frontend\dist\index.html"
if (-not (Test-Path $distPath)) {
    Write-Host "`nFrontend production build missing. Compiling React SPA..." -ForegroundColor Yellow
    Push-Location (Join-Path $PSScriptRoot "frontend")
    npm run build
    Pop-Location
    Write-Host "Frontend build completed successfully." -ForegroundColor Green
} else {
    Write-Host "`nFound existing frontend build in frontend/dist." -ForegroundColor Green
}

$backendPath = Join-Path $PSScriptRoot "backend"
Write-Host "`nStarting Multi-Threaded Waitress WSGI Server on port 5000..." -ForegroundColor Cyan
Write-Host "Single-Port Deployment: REST API + React SPA" -ForegroundColor Gray
Write-Host "  - Local URL  : http://localhost:5000" -ForegroundColor White
Write-Host "  - Health URL : http://localhost:5000/api/v1/health" -ForegroundColor White
Write-Host "  - SQL Server : http://localhost:5000/api/v1/health/db" -ForegroundColor White

Set-Location $backendPath
python wsgi_server.py
