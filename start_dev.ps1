Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  Launching AI Pothole Detection Platform in Development Mode" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$backendPath = Join-Path $PSScriptRoot "backend"
$frontendPath = Join-Path $PSScriptRoot "frontend"

Write-Host "`n[1/2] Starting Flask Backend on port 5000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$backendPath'; python run.py"

Start-Sleep -Seconds 2

Write-Host "[2/2] Starting Vite React Frontend on port 5173..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$frontendPath'; npm run dev"

Write-Host "`nServices started in separate PowerShell windows:" -ForegroundColor Yellow
Write-Host "  - Backend API : http://127.0.0.1:5000" -ForegroundColor White
Write-Host "  - Frontend UI : http://localhost:5173" -ForegroundColor White
Write-Host "Press any key to close this launcher window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
