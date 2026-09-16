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

echo [3/3] Launching Public Tunnel (bore)...
echo ======================================================================
echo   Starting tunnel to bore.pub on Port 1433...
echo   (Zero setup required - No credit card, no account)
echo ======================================================================
echo.

"%~dp0bore.exe" local 1433 --to bore.pub

pause
