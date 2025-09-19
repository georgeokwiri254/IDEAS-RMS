#!/usr/bin/env python3
"""
SUPER SIMPLE LAUNCHER for Grand Millennium Dubai RMS
Just works - no complex port management, just launches the app
"""

import subprocess
import sys
import os
from pathlib import Path
import time

def main():
    print("🏨 GRAND MILLENNIUM DUBAI - RMS LAUNCHER")
    print("=" * 50)

    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # Check if we have virtual environment
    venv_python = "venv/bin/python"
    if not Path(venv_python).exists():
        print("❌ Virtual environment not found")
        print("💡 Try running: python3 -m venv venv")
        return 1

    # Check if database exists
    if not Path("data/rms.db").exists():
        print("🔧 Setting up database...")
        try:
            subprocess.run([venv_python, "setup_database.py"], check=True)
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

    # Try different ports
    ports = [8501, 8502, 8503, 8504, 8505]

    for port in ports:
        print(f"🚀 Trying to start on port {port}...")

        try:
            # Start streamlit
            process = subprocess.Popen([
                venv_python, "-m", "streamlit", "run", app_file,
                "--server.port", str(port),
                "--server.address", "localhost",
                "--browser.gatherUsageStats", "false"
            ])

            # Wait a moment
            time.sleep(2)

            # Check if it's still running
            if process.poll() is None:
                print("🎉 SUCCESS!")
                print(f"🌐 Open: http://localhost:{port}")
                print("🏨 Grand Millennium Dubai RMS is running!")
                print("\nPress Ctrl+C to stop")

                try:
                    process.wait()
                except KeyboardInterrupt:
                    print("\n🛑 Stopping...")
                    process.terminate()
                    time.sleep(1)
                    if process.poll() is None:
                        process.kill()

                return 0
            else:
                print(f"❌ Port {port} failed")

        except Exception as e:
            print(f"❌ Error on port {port}: {e}")
            continue

    print("❌ Could not start on any port")
    return 1

if __name__ == "__main__":
    sys.exit(main())