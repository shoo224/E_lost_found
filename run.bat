@echo off
REM E Lost & Found - Run backend (FastAPI)
REM Double-click or run: run.bat

set "ROOT=%~dp0"
set "BACKEND=%ROOT%backend"
cd /d "%BACKEND%"

REM Create venv if it doesn't exist (use py launcher first - works when python not on PATH)
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    py -m venv venv 2>nul
    if errorlevel 1 (
        python -m venv venv 2>nul
    )
    if not exist "venv\Scripts\activate.bat" (
        echo Failed to create venv. Install Python from python.org and ensure "py" or "python" works in a new cmd.
        pause
        exit /b 1
    )
)

REM Activate venv (quoted path in case folder has &)
call "venv\Scripts\activate.bat"

REM Install dependencies if fastapi is missing
"%BACKEND%\venv\Scripts\python.exe" -c "import fastapi" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    "%BACKEND%\venv\Scripts\pip.exe" install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install requirements.
        pause
        exit /b 1
    )
    echo.
)

REM Run FastAPI with uvicorn (use venv Python so fastapi is found)
echo Starting E Lost and Found API on http://localhost:8000
echo API docs: http://localhost:8000/docs
echo.
"%BACKEND%\venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
