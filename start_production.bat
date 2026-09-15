@echo off
TITLE AI Pothole Detection - Production Mode
echo ======================================================================
echo Launching AI Pothole Detection Platform in Production Mode
echo ======================================================================

REM Check if frontend build exists, build if missing
if not exist "frontend\dist\index.html" (
    echo Compiling React Single-Page Application for production...
    cd frontend
    call npm run build
    cd ..
    echo Frontend build complete.
) else (
    echo Frontend production build found in frontend\dist.
)

echo.
echo Starting Multi-Threaded Waitress WSGI Server on port 5000...
echo Single-Port Architecture: REST API + React SPA served together.
echo.
echo Access URL: http://localhost:5000
echo Health URL: http://localhost:5000/api/v1/health
echo.

cd backend
python wsgi_server.py
pause

