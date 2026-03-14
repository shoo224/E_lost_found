@echo off
REM E Lost & Found - Serve frontend (HTML/CSS/JS) on port 5500
REM Open http://localhost:5500 in your browser. API runs on port 8000 (run.bat).

set "ROOT=%~dp0"
set "FRONTEND=%ROOT%frontend"
cd /d "%FRONTEND%"

echo Serving E Lost and Found frontend at http://localhost:5500
echo Open this in your browser. Make sure the API is running (run.bat) on port 8000.
echo.
py -m http.server 5500 2>nul
if errorlevel 1 python -m http.server 5500
pause
