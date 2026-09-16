@echo off
title AI Pothole Detection - SQL Server Bridge
color 0A
echo ======================================================================
echo    AI POTHOLE DETECTION - LOCAL SQL SERVER TO RENDER BRIDGE
echo ======================================================================
echo.

echo [1/3] Restarting SQL Server (SQLEXPRESS) to activate TCP Port 1433...
powershell -Command "Restart-Service -Name 'MSSQL$SQLEXPRESS' -Force"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [NOTE] If access is denied, please close and Right-Click this file
    echo        and choose 'Run as Administrator'.
    echo.
) else (
    echo [OK] SQL Server Express restarted successfully!
)

echo.
echo [2/3] Verifying TCP Port 1433 is listening...
powershell -Command "$m = netstat -ano | findstr :1433; if ($m) { Write-Host '[OK] Port 1433 is active and LISTENING!' -ForegroundColor Green } else { Write-Host '[!] Port 1433 is not active yet.' -ForegroundColor Yellow }"

echo.
echo [3/3] Launching ngrok TCP tunnel...
set NGROK_BIN="%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe"

%NGROK_BIN% tcp 1433
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ======================================================================
    echo   ACTION REQUIRED: ngrok needs your free authtoken (one-time setup)
    echo ======================================================================
    echo   1. Get your free token at: https://dashboard.ngrok.com/get-started/your-authtoken
    echo   2. Paste your authtoken below and press Enter:
    set /p AUTHTOKEN="Enter ngrok authtoken: "
    if defined AUTHTOKEN (
        %NGROK_BIN% config add-authtoken %AUTHTOKEN%
        echo.
        echo [OK] Token saved! Launching tunnel now...
        %NGROK_BIN% tcp 1433
    )
)
pause
