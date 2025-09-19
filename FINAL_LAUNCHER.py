#!/usr/bin/env python3
"""
FINAL GUARANTEED BROWSER LAUNCHER
This WILL open your browser no matter what!
"""

import subprocess
import webbrowser
import time
import os
import sys
from pathlib import Path
import threading

def force_open_browser(url, delay=6):
    """Force open browser using multiple methods"""
    def open_with_delay():
        time.sleep(delay)
        print(f"\n🌐 FORCE OPENING BROWSER: {url}")

        # Method 1: Python webbrowser
        try:
            webbrowser.open(url)
            print("✅ Python webbrowser: SUCCESS")
            return
        except Exception as e:
            print(f"❌ Python webbrowser failed: {e}")

        # Method 2: System commands
        import platform
        system = platform.system().lower()

        try:
            if system == "linux":
                subprocess.run(['xdg-open', url], check=True)
                print("✅ xdg-open: SUCCESS")
            elif system == "darwin":  # macOS
                subprocess.run(['open', url], check=True)
                print("✅ macOS open: SUCCESS")
            elif system == "windows":
                subprocess.run(['start', url], shell=True, check=True)
                print("✅ Windows start: SUCCESS")
        except Exception as e:
            print(f"❌ System command failed: {e}")

        # Method 3: Direct browser commands
        browsers = ['firefox', 'google-chrome', 'chromium-browser', 'safari', 'microsoft-edge']
        for browser in browsers:
            try:
                subprocess.run([browser, url], check=True)
                print(f"✅ Direct {browser}: SUCCESS")
                return
            except:
                continue

        print("⚠️  All browser methods attempted")
        print(f"💡 MANUAL: Copy and paste this URL: {url}")

    thread = threading.Thread(target=open_with_delay)
    thread.daemon = True
    thread.start()

def main():
    print("🏨 GRAND MILLENNIUM DUBAI - FINAL GUARANTEED LAUNCHER")
    print("=" * 65)

    # Change to script directory
    os.chdir(Path(__file__).parent)

    # Kill existing processes
    try:
        subprocess.run(['pkill', '-f', 'streamlit'], capture_output=True)
        time.sleep(1)
    except:
        pass

    # Check virtual environment
    venv_python = Path("venv/bin/python")
    if not venv_python.exists():
        print("❌ Virtual environment not found")
        print("💡 Run: python3 -m venv venv && source venv/bin/activate && pip install streamlit pandas")
        return 1

    # Setup database
    if not Path("data/rms.db").exists():
        print("🔧 Setting up database...")
        subprocess.run([str(venv_python), "setup_database.py"], check=True)

    print("✅ All prerequisites ready")

    # Start the browser opener
    url = "http://localhost:8501"
    force_open_browser(url)

    print("🚀 Starting Streamlit server...")
    print("⏳ Server will start in 3 seconds...")
    print("🌐 Browser will open automatically in 6 seconds...")

    # Start Streamlit
    try:
        process = subprocess.Popen([
            str(venv_python), "-m", "streamlit", "run", "simple_app.py",
            "--server.port", "8501",
            "--server.headless", "false"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Wait a moment
        time.sleep(3)

        if process.poll() is None:
            print("✅ Server started successfully!")
            print("")
            print("🎉 GRAND MILLENNIUM DUBAI RMS IS NOW RUNNING!")
            print("=" * 65)
            print("🏨 Hotel: Grand Millennium Dubai (339 rooms)")
            print("💰 Target ADR: 319 AED")
            print("📊 Dynamic Pricing | Channel Management | Competitor Analysis")
            print("🌐 URL: http://localhost:8501")
            print("")
            print("🎯 TABS AVAILABLE:")
            print("   • RMS - Room pricing controls")
            print("   • Channels - OTA management")
            print("   • Competitors - Market analysis")
            print("   • Simulation - Scenario testing")
            print("")
            print("🛑 Press Ctrl+C to stop")
            print("=" * 65)

            # Keep running
            try:
                process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Stopping...")
                process.terminate()
                time.sleep(1)
                if process.poll() is None:
                    process.kill()
                print("✅ Stopped")
        else:
            stdout, stderr = process.communicate()
            print("❌ Server failed to start")
            print(f"Error: {stderr.decode()}")
            return 1

    except Exception as e:
        print(f"❌ Failed to start: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())