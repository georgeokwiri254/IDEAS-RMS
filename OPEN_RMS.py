#!/usr/bin/env python3
"""
BROWSER-OPENING LAUNCHER for Grand Millennium Dubai RMS
This WILL open your browser automatically!
"""

import subprocess
import webbrowser
import time
import os
import sys
from pathlib import Path
import socket
import threading

def check_port_open(port, timeout=30):
    """Check if port is responding"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                if sock.connect_ex(('localhost', port)) == 0:
                    return True
        except:
            pass
        time.sleep(0.5)
    return False

def open_browser_delayed(url, delay=3):
    """Open browser after a delay"""
    def delayed_open():
        time.sleep(delay)
        print(f"🌐 Opening browser to: {url}")
        try:
            webbrowser.open(url)
            print("✅ Browser opened successfully!")
        except Exception as e:
            print(f"❌ Could not open browser: {e}")
            print(f"💡 Please manually open: {url}")

    thread = threading.Thread(target=delayed_open)
    thread.daemon = True
    thread.start()

def main():
    print("🏨 GRAND MILLENNIUM DUBAI - BROWSER-OPENING RMS LAUNCHER")
    print("=" * 60)

    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # Kill any existing streamlit processes
    print("🔧 Cleaning up any existing processes...")
    try:
        subprocess.run(['pkill', '-f', 'streamlit'], capture_output=True)
        time.sleep(1)
    except:
        pass

    # Check virtual environment
    venv_python = Path("venv/bin/python")
    if not venv_python.exists():
        print("❌ Virtual environment not found")
        print("💡 Please run: python3 -m venv venv && source venv/bin/activate && pip install streamlit pandas numpy plotly")
        return 1

    # Setup database if needed
    if not Path("data/rms.db").exists():
        print("🔧 Setting up database...")
        try:
            subprocess.run([str(venv_python), "setup_database.py"], check=True)
            print("✅ Database ready")
        except subprocess.CalledProcessError:
            print("❌ Database setup failed")
            return 1
    else:
        print("✅ Database found")

    # Choose app file
    if Path("simple_app.py").exists():
        app_file = "simple_app.py"
    elif Path("app.py").exists():
        app_file = "app.py"
    else:
        print("❌ No app file found")
        return 1

    print(f"📱 Using: {app_file}")

    # Find available port
    port = 8501
    while port <= 8510:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('localhost', port))
                break
        except OSError:
            port += 1

    if port > 8510:
        print("❌ No available ports found")
        return 1

    print(f"🚀 Starting RMS on port {port}...")

    # URL for browser
    url = f"http://localhost:{port}"

    # Start browser opening in background
    open_browser_delayed(url, delay=5)

    try:
        # Start Streamlit with explicit browser settings
        process = subprocess.Popen([
            str(venv_python), "-m", "streamlit", "run", app_file,
            "--server.port", str(port),
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false",
            "--server.headless", "false"  # This should open browser
        ])

        print(f"🌐 RMS URL: {url}")
        print("⏳ Waiting for server to start...")

        # Wait for port to be available
        if check_port_open(port, timeout=30):
            print("✅ Server is running!")
            print(f"🎉 Grand Millennium Dubai RMS is ready!")
            print(f"🏨 339 rooms | Target ADR: 319 AED")
            print(f"📊 Features: Dynamic Pricing | Channel Management | Competitor Analysis")
            print("")
            print("🌐 If browser didn't open automatically, go to:")
            print(f"   {url}")
            print("")
            print("🛑 Press Ctrl+C to stop")
            print("=" * 60)

            # Try opening browser again if not opened yet
            time.sleep(2)
            try:
                webbrowser.open(url)
            except:
                pass

            # Wait for process
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Stopping RMS...")
                process.terminate()
                time.sleep(1)
                if process.poll() is None:
                    process.kill()
                print("✅ Stopped")

        else:
            print("❌ Server failed to start properly")
            process.terminate()
            return 1

    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())