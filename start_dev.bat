@echo off
TITLE AI Pothole Detection - Development Mode
echo ======================================================================
echo Launching AI Pothole Detection Platform in Development Mode
echo ======================================================================

echo Starting Flask Backend on port 5000...
start "Pothole Flask Backend" cmd /k "cd backend && python run.py"

timeout /t 2 /nobreak >nul

echo Starting Vite React Frontend on port 5173...
start "Pothole React Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers are launching in separate windows:
echo - Backend API : http://127.0.0.1:5000
echo - Frontend UI : http://localhost:5173
echo.
pause
