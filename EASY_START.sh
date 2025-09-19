#!/bin/bash

# SUPER EASY LAUNCHER - Just double-click or run this!

cd "$(dirname "$0")"

echo "🏨 STARTING GRAND MILLENNIUM DUBAI RMS..."
echo ""

# Quick setup if needed
if [ ! -f "data/rms.db" ]; then
    echo "🔧 First time setup..."
    python3 setup_database.py
fi

echo "🚀 Launching RMS..."
echo "🌐 Will open at: http://localhost:8501"
echo "💡 Press Ctrl+C to stop"
echo ""

# Start with virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    python -m streamlit run simple_app.py --server.port 8501 --browser.gatherUsageStats false
else
    # Try with system python
    python3 -m streamlit run simple_app.py --server.port 8501 --browser.gatherUsageStats false
fi