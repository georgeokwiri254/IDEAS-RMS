@echo off
REM Smart Launcher for Grand Millennium Dubai RMS (Windows)
REM Automatically handles port management and launches application

echo ================================================================
echo 🏨 GRAND MILLENNIUM DUBAI - RMS SMART LAUNCHER
echo ================================================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Step 1: Setup database if needed
if not exist "data\rms.db" (
    echo 🔧 Database not found. Setting up...
    python setup_database.py
    if errorlevel 1 (
        echo ❌ Database setup failed
        pause
        exit /b 1
    )
) else (
    echo ✅ Database found
)

REM Step 2: Check and install dependencies
echo 📦 Checking dependencies...
python -c "import streamlit, pandas, numpy" 2>nul
if errorlevel 1 (
    echo 📥 Installing missing packages...
    pip install --quiet streamlit pandas numpy plotly
    if errorlevel 1 (
        echo ⚠️ Package installation failed. Continuing anyway...
    )
)
echo ✅ Dependencies checked

REM Step 3: Kill processes on common ports
echo.
echo 🔧 Managing ports...
echo 🔍 Killing processes on common Streamlit ports...

REM Kill processes on ports 8501-8503
for %%p in (8501 8502 8503) do (
    echo Checking port %%p...
    netstat -ano | findstr :%%p | findstr LISTENING >nul
    if not errorlevel 1 (
        echo ⚠️ Found process on port %%p, attempting to kill...
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%%p ^| findstr LISTENING') do (
            taskkill /PID %%a /F >nul 2>&1
        )
    )
)

REM Step 4: Find available port
echo.
echo 🔍 Finding available port...
set "available_port="

for %%p in (8501 8502 8503 8504 8505) do (
    netstat -ano | findstr :%%p | findstr LISTENING >nul
    if errorlevel 1 (
        if not defined available_port (
            set "available_port=%%p"
        )
    )
)

if not defined available_port (
    echo ❌ No available ports found in range 8501-8505
    pause
    exit /b 1
)

echo ✅ Using port %available_port%

REM Step 5: Determine app file
set "app_file=simple_app.py"
if not exist "%app_file%" (
    set "app_file=app.py"
)

if not exist "%app_file%" (
    echo ❌ No application file found ^(simple_app.py or app.py^)
    pause
    exit /b 1
)

REM Step 6: Launch application
echo.
echo 🚀 Starting RMS application...
echo 📱 App file: %app_file%
echo 🌐 Port: %available_port%
echo.

echo ================================================================
echo 🎉 LAUNCHING GRAND MILLENNIUM DUBAI RMS
echo ================================================================
echo 🌐 URL: http://localhost:%available_port%
echo 🏨 Hotel: Grand Millennium Dubai ^(339 rooms^)
echo 💰 Target ADR: 319 AED
echo 📊 Features: Dynamic Pricing ^| Channel Management ^| Competitor Analysis
echo.
echo Press Ctrl+C to stop the application
echo ================================================================
echo.

REM Launch Streamlit
python -m streamlit run "%app_file%" --server.port %available_port% --server.address localhost --browser.gatherUsageStats false --server.headless true

REM Cleanup on exit
echo.
echo 🛑 Shutting down RMS...
echo 🧹 Cleanup completed
pause