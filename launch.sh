#!/bin/bash

# Simple Smart Launcher for Grand Millennium Dubai RMS
# Automatically kills ports and finds next available port

echo "================================================================"
echo "🏨 GRAND MILLENNIUM DUBAI - RMS SMART LAUNCHER"
echo "================================================================"
echo ""

# Function to kill processes on a port
kill_port() {
    local port=$1
    echo "🔍 Checking port $port..."

    # Find processes using the port
    local pids=$(lsof -ti:$port 2>/dev/null)

    if [ -n "$pids" ]; then
        echo "⚠️  Found processes on port $port: $pids"
        echo "🔧 Killing processes..."

        # Kill the processes
        echo $pids | xargs kill -TERM 2>/dev/null
        sleep 2

        # Force kill if still running
        local remaining=$(lsof -ti:$port 2>/dev/null)
        if [ -n "$remaining" ]; then
            echo "💀 Force killing remaining processes..."
            echo $remaining | xargs kill -KILL 2>/dev/null
            sleep 1
        fi

        echo "✅ Port $port cleared"
    else
        echo "✅ Port $port is free"
    fi
}

# Function to check if port is available
is_port_available() {
    local port=$1
    ! nc -z localhost $port 2>/dev/null
}

# Function to find next available port
find_available_port() {
    local start_port=${1:-8501}
    local max_attempts=${2:-10}

    for ((i=0; i<max_attempts; i++)); do
        local port=$((start_port + i))
        if is_port_available $port; then
            echo $port
            return 0
        fi
    done

    return 1
}

# Change to script directory
cd "$(dirname "$0")"

# Step 1: Setup database if needed
if [ ! -f "data/rms.db" ]; then
    echo "🔧 Database not found. Setting up..."
    python3 setup_database.py
    if [ $? -ne 0 ]; then
        echo "❌ Database setup failed"
        exit 1
    fi
else
    echo "✅ Database found"
fi

# Step 2: Check Python packages
echo "📦 Checking dependencies..."
python3 -c "import streamlit, pandas, numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📥 Installing missing packages..."
    pip3 install --quiet streamlit pandas numpy plotly 2>/dev/null || {
        echo "⚠️  Package installation failed. Continuing anyway..."
    }
fi
echo "✅ Dependencies checked"

# Step 3: Kill processes on common Streamlit ports
echo ""
echo "🔧 Managing ports..."
kill_port 8501
kill_port 8502
kill_port 8503

# Step 4: Find available port
echo ""
echo "🔍 Finding available port..."
available_port=$(find_available_port 8501 10)

if [ -z "$available_port" ]; then
    echo "❌ No available ports found in range 8501-8510"
    exit 1
fi

echo "✅ Using port $available_port"

# Step 5: Determine which app file to use
app_file="simple_app.py"
if [ ! -f "$app_file" ]; then
    app_file="app.py"
fi

if [ ! -f "$app_file" ]; then
    echo "❌ No application file found (simple_app.py or app.py)"
    exit 1
fi

# Step 6: Launch Streamlit
echo ""
echo "🚀 Starting RMS application..."
echo "📱 App file: $app_file"
echo "🌐 Port: $available_port"
echo ""

# Function to handle cleanup
cleanup() {
    echo ""
    echo "🛑 Shutting down RMS..."

    # Kill any remaining streamlit processes
    pkill -f "streamlit.*$app_file" 2>/dev/null
    kill_port $available_port

    echo "🧹 Cleanup completed"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Launch Streamlit
echo "================================================================"
echo "🎉 LAUNCHING GRAND MILLENNIUM DUBAI RMS"
echo "================================================================"
echo "🌐 URL: http://localhost:$available_port"
echo "🏨 Hotel: Grand Millennium Dubai (339 rooms)"
echo "💰 Target ADR: 319 AED"
echo "📊 Features: Dynamic Pricing | Channel Management | Competitor Analysis"
echo ""
echo "Press Ctrl+C to stop the application"
echo "================================================================"
echo ""

# Start Streamlit
python3 -m streamlit run "$app_file" \
    --server.port $available_port \
    --server.address localhost \
    --browser.gatherUsageStats false \
    --server.headless true

# If we get here, Streamlit has stopped
cleanup