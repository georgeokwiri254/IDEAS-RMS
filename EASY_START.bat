@echo off
REM SUPER EASY LAUNCHER - Just double-click this!

echo 🏨 STARTING GRAND MILLENNIUM DUBAI RMS...
echo.

REM Change to script directory
cd /d "%~dp0"

REM Quick setup if needed
if not exist "data\rms.db" (
    echo 🔧 First time setup...
    python setup_database.py
)

echo 🚀 Launching RMS...
echo 🌐 Will open at: http://localhost:8501
echo 💡 Press Ctrl+C to stop
echo.

REM Try with virtual environment first
if exist "venv\Scripts\python.exe" (
    echo Using virtual environment...
    call venv\Scripts\activate.bat
    python -m streamlit run simple_app.py --server.port 8501 --browser.gatherUsageStats false
) else (
    echo Using system Python...
    python -m streamlit run simple_app.py --server.port 8501 --browser.gatherUsageStats false
)

pause