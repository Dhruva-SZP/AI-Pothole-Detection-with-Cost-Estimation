@echo off
setlocal enabledelayedexpansion
title AI Pothole Detection - SQL Server Bridge
color 0A

:: 1. Check for Administrator Privileges and Auto-Elevate
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Requesting Administrator privileges to manage SQL Server service...
    powershell -Command "Start-Process cmd -ArgumentList '/k `\"%~f0`\"' -Verb RunAs"
    exit /b
)

echo ======================================================================
echo    AI POTHOLE DETECTION - LOCAL SQL SERVER TO RENDER BRIDGE
echo ======================================================================
echo.

echo [1/3] Restarting SQL Server (SQLEXPRESS) to activate TCP Port 1433...
net stop "MSSQL$SQLEXPRESS" >nul 2>&1
net start "MSSQL$SQLEXPRESS"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Could not start MSSQL$SQLEXPRESS service automatically.
    echo     Please verify SQL Server is installed and running.
) else (
    echo [OK] SQL Server Express restarted and active!
)

echo.
echo [2/3] Verifying TCP Port 1433 is listening...
powershell -Command "$m = netstat -ano | findstr :1433; if ($m) { Write-Host '[OK] Port 1433 is active and LISTENING!' -ForegroundColor Green } else { Write-Host '[!] Port 1433 is not listening yet. Check SQL Server Configuration Manager.' -ForegroundColor Yellow }"

echo.
echo [3/3] Preparing ngrok TCP tunnel...
set NGROK_BIN="%LOCALAPPDATA%\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe"

if not exist %NGROK_BIN% (
    echo [!] ngrok.exe was not found at standard winget path.
    echo     Checking system PATH...
    set NGROK_BIN=ngrok
)

:: Check if ngrok config exists
%NGROK_BIN% config check >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo.
    echo ======================================================================
    echo   ACTION REQUIRED: ngrok needs your free authtoken (one-time setup)
    echo ======================================================================
    echo   1. Sign in or sign up (free) at: https://dashboard.ngrok.com
    echo   2. Get your authtoken at: https://dashboard.ngrok.com/get-started/your-authtoken
    echo   3. Paste your authtoken below and press Enter:
    echo ======================================================================
    set /p AUTHTOKEN="Enter ngrok authtoken: "
    if defined AUTHTOKEN (
        %NGROK_BIN% config add-authtoken !AUTHTOKEN!
        echo.
        echo [OK] Token saved successfully!
    )
)

echo.
echo ======================================================================
echo   STARTING NGROK TUNNEL (Port 1433)...
echo   When the tunnel starts, look for the 'Forwarding' line:
echo      Example:  Forwarding  tcp://0.tcp.ngrok.io:19456 -^> localhost:1433
echo.
echo   Then in your Render Dashboard -^> Environment, set:
echo      DB_SERVER = 0.tcp.ngrok.io   (or whatever host ngrok shows)
echo      DB_PORT   = 19456            (or whatever port ngrok shows)
echo      DB_NAME   = PotholeDetectionDB
echo      DB_USER   = pothole_app
echo      DB_PASSWORD = PotholeSecure2026!
echo      DB_TRUSTED_CONNECTION = no
echo ======================================================================
echo.
%NGROK_BIN% tcp 1433

pause
