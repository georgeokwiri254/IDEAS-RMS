# 🚀 Grand Millennium Dubai RMS - Smart Launcher Guide

## Overview

The RMS system now includes **smart launchers** that automatically handle port management and application startup. These launchers will:

- ✅ **Kill any processes** blocking common Streamlit ports (8501-8505)
- ✅ **Find the next available port** automatically
- ✅ **Set up the database** if it doesn't exist
- ✅ **Install missing dependencies** automatically
- ✅ **Launch the application** with proper configuration
- ✅ **Handle cleanup** on exit (Ctrl+C)

## 🎯 Quick Start Options

### Option 1: Python Launcher (Recommended)
```bash
cd "IDEAS RMS"
python3 launch_rms.py
```

### Option 2: Shell Script (Linux/Mac)
```bash
cd "IDEAS RMS"
./launch.sh
```

### Option 3: Batch File (Windows)
```cmd
cd "IDEAS RMS"
launch.bat
```

## 🔧 What Each Launcher Does

### 1. **Smart Port Management**
- Checks ports 8501, 8502, 8503 for running processes
- Kills any blocking processes (usually old Streamlit instances)
- Finds the next available port in range 8501-8510
- Handles graceful shutdown on Ctrl+C

### 2. **Automatic Setup**
- Verifies database exists (`data/rms.db`)
- Runs database setup if needed
- Checks for required Python packages
- Installs missing dependencies automatically

### 3. **Application Launch**
- Chooses the best app file (`simple_app.py` or `app.py`)
- Starts Streamlit with optimal configuration
- Provides clear access URL and system information
- Monitors the application process

## 🖥️ Launcher Output Example

```
================================================================
🏨 GRAND MILLENNIUM DUBAI - RMS SMART LAUNCHER
================================================================

✅ Database found
📦 Checking dependencies...
✅ All dependencies available

🔧 Managing ports...
🔍 Checking port 8501...
⚠️  Port 8501 is busy
   Killing process 12345...
✅ Port 8501 is now free
✅ Using port 8501

🚀 Starting RMS application...

================================================================
🎉 RMS IS NOW RUNNING!
================================================================
🌐 URL: http://localhost:8501
🏨 Hotel: Grand Millennium Dubai (339 rooms)
💰 Target ADR: 319 AED
📊 Features: Dynamic Pricing | Channel Management | Competitor Analysis

Press Ctrl+C to stop the application
================================================================
```

## 🛠️ Advanced Features

### Python Launcher (`launch_rms.py`)
- **Most robust**: Complete error handling and process management
- **Cross-platform**: Works on Linux, Mac, and Windows
- **Detailed logging**: Shows exactly what's happening
- **Signal handling**: Proper cleanup on interruption
- **Process tracking**: Monitors launched applications

### Shell Script (`launch.sh`)
- **Fast startup**: Optimized for Unix-like systems
- **Lightweight**: Minimal dependencies
- **Native tools**: Uses system commands (lsof, netstat)
- **Simple**: Easy to modify and customize

### Batch File (`launch.bat`)
- **Windows native**: Designed specifically for Windows
- **Command prompt**: Works with Windows CMD
- **Port management**: Uses netstat and taskkill
- **User-friendly**: Clear output and error messages

## 🔍 Troubleshooting

### Port Issues
If ports are still blocked after launcher attempts:
```bash
# Manual port cleanup (Linux/Mac)
sudo lsof -ti:8501 | xargs sudo kill -9

# Manual port cleanup (Windows)
netstat -ano | findstr :8501
taskkill /PID [PID_NUMBER] /F
```

### Permission Issues
If launcher can't kill processes:
```bash
# Run with elevated permissions (Linux/Mac)
sudo python3 launch_rms.py

# Run as Administrator (Windows)
# Right-click Command Prompt -> "Run as Administrator"
launch.bat
```

### Database Issues
If database setup fails:
```bash
# Manual database setup
python3 setup_database.py

# Check database status
python3 -c "
import sqlite3
conn = sqlite3.connect('data/rms.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM inventory')
print(f'Rooms: {cursor.fetchone()[0]}')
conn.close()
"
```

### Dependency Issues
If packages can't be installed:
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install manually
pip install streamlit pandas numpy plotly sqlalchemy
```

## 🎯 Recommended Usage

### For Development
```bash
python3 launch_rms.py
```
- Best for testing and development
- Complete error reporting
- Easy to debug issues

### For Quick Demo
```bash
./launch.sh
```
- Fastest startup
- Minimal overhead
- Good for presentations

### For Windows Users
```cmd
launch.bat
```
- Native Windows experience
- Works without WSL or Git Bash
- Familiar interface

## 🔄 Multiple Instances

The launchers support running multiple RMS instances:
- **First instance**: Usually gets port 8501
- **Second instance**: Automatically uses port 8502
- **Third instance**: Automatically uses port 8503
- And so on...

Each instance runs independently with its own database connection.

## 🛑 Stopping the Application

### Graceful Shutdown
- Press **Ctrl+C** in the terminal
- Launcher will clean up processes automatically
- Database connections closed properly

### Force Stop
```bash
# If graceful shutdown fails
pkill -f streamlit  # Linux/Mac
taskkill /IM python.exe /F  # Windows
```

## 🎉 Success Indicators

When the launcher works correctly, you'll see:
- ✅ Database verification
- ✅ Port management completion
- ✅ Dependency confirmation
- 🌐 Clear access URL
- 📊 System status display

Access the RMS at the provided URL (usually `http://localhost:8501`) and you'll see the full Grand Millennium Dubai Revenue Management System interface.

---

**Ready to launch your RMS!** Choose any launcher method above and start managing revenue for Grand Millennium Dubai's 339 rooms! 🏨💰