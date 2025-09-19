#!/bin/bash

# Grand Millennium Dubai RMS Startup Script

echo "=================================================="
echo "GRAND MILLENNIUM DUBAI - REVENUE MANAGEMENT SYSTEM"
echo "=================================================="
echo ""

# Check if database exists
if [ ! -f "data/rms.db" ]; then
    echo "🔧 Database not found. Setting up..."
    python3 setup_database.py
    echo ""
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
    echo ""
fi

# Activate virtual environment and install requirements
echo "📦 Installing/updating dependencies..."
source venv/bin/activate

# Install basic packages needed
pip install --quiet streamlit pandas sqlite3 > /dev/null 2>&1

echo "✅ Environment ready!"
echo ""

# Check database status
echo "📊 Database Status:"
python3 -c "
import sqlite3
conn = sqlite3.connect('data/rms.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM inventory')
rooms = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM bookings')
bookings = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM competitor_rates')
comp_rates = cursor.fetchone()[0]
print(f'   Rooms: {rooms}')
print(f'   Bookings: {bookings}')
print(f'   Competitor Rates: {comp_rates}')
conn.close()
"

echo ""
echo "🚀 Starting RMS Application..."
echo "   URL: http://localhost:8501"
echo "   Press Ctrl+C to stop"
echo ""

# Start Streamlit app
streamlit run simple_app.py --server.port 8501 --server.address localhost