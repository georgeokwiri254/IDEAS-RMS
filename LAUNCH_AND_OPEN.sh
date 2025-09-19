#!/bin/bash

echo "🏨 GRAND MILLENNIUM DUBAI - RMS LAUNCHER WITH BROWSER"
echo "============================================================"

cd "$(dirname "$0")"

# Kill any existing streamlit
pkill -f streamlit 2>/dev/null || true
sleep 1

# Setup database if needed
if [ ! -f "data/rms.db" ]; then
    echo "🔧 Setting up database..."
    python3 setup_database.py
fi

echo "🚀 Starting RMS server..."
echo "⏳ Please wait 5 seconds for server startup..."

# Start streamlit in background
if [ -d "venv" ]; then
    source venv/bin/activate
    nohup python -m streamlit run simple_app.py --server.port 8501 --browser.gatherUsageStats false > /dev/null 2>&1 &
else
    nohup python3 -m streamlit run simple_app.py --server.port 8501 --browser.gatherUsageStats false > /dev/null 2>&1 &
fi

# Get the process ID
STREAMLIT_PID=$!

# Wait for server to start
sleep 5

# Check if server is running
if kill -0 $STREAMLIT_PID 2>/dev/null; then
    echo "✅ Server started successfully!"
    echo ""
    echo "🌐 Opening browser to: http://localhost:8501"

    # Try multiple browser opening methods
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open http://localhost:8501
    elif command -v open >/dev/null 2>&1; then
        open http://localhost:8501
    elif command -v firefox >/dev/null 2>&1; then
        firefox http://localhost:8501 &
    elif command -v google-chrome >/dev/null 2>&1; then
        google-chrome http://localhost:8501 &
    elif command -v chromium-browser >/dev/null 2>&1; then
        chromium-browser http://localhost:8501 &
    else
        echo "❌ Could not detect browser"
        echo "💡 Please manually open: http://localhost:8501"
    fi

    echo ""
    echo "🎉 GRAND MILLENNIUM DUBAI RMS IS RUNNING!"
    echo "============================================================"
    echo "🏨 Hotel: Grand Millennium Dubai (339 rooms)"
    echo "💰 Target ADR: 319 AED"
    echo "📊 Features: Dynamic Pricing | Channel Management | Competitor Analysis"
    echo ""
    echo "🌐 URL: http://localhost:8501"
    echo "🛑 Press Ctrl+C to stop (or close this terminal)"
    echo "============================================================"

    # Function to cleanup on exit
    cleanup() {
        echo ""
        echo "🛑 Stopping RMS server..."
        kill $STREAMLIT_PID 2>/dev/null
        pkill -f streamlit 2>/dev/null
        echo "✅ Server stopped"
        exit 0
    }

    # Set trap for cleanup
    trap cleanup SIGINT SIGTERM EXIT

    # Keep script running
    wait $STREAMLIT_PID

else
    echo "❌ Failed to start server"
    exit 1
fi