#!/usr/bin/env python3
"""
Smart Launcher for Grand Millennium Dubai RMS
Automatically handles port management and launches the application
"""

import subprocess
import socket
import time
import os
import sys
import signal
from pathlib import Path

class RMSLauncher:
    def __init__(self):
        self.default_ports = [8501, 8502, 8503, 8504, 8505]
        self.streamlit_processes = []

    def find_processes_on_port(self, port):
        """Find processes running on a specific port"""
        try:
            # Use netstat to find processes on port
            result = subprocess.run(
                ['netstat', '-tlnp'],
                capture_output=True,
                text=True,
                check=True
            )

            processes = []
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTEN' in line:
                    parts = line.split()
                    if len(parts) >= 7:
                        pid_info = parts[6]
                        if '/' in pid_info:
                            pid = pid_info.split('/')[0]
                            if pid.isdigit():
                                processes.append(int(pid))

            return processes
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback method using lsof if netstat fails
            try:
                result = subprocess.run(
                    ['lsof', '-ti', f':{port}'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return [int(pid) for pid in result.stdout.strip().split('\n') if pid.strip()]
                return []
            except (subprocess.CalledProcessError, FileNotFoundError):
                return []

    def kill_port(self, port):
        """Kill all processes running on a specific port"""
        processes = self.find_processes_on_port(port)

        if not processes:
            return True

        print(f"🔧 Found {len(processes)} process(es) on port {port}")

        for pid in processes:
            try:
                print(f"   Killing process {pid}...")
                os.kill(pid, signal.SIGTERM)
                time.sleep(1)

                # Check if process still exists
                try:
                    os.kill(pid, 0)
                    print(f"   Force killing process {pid}...")
                    os.kill(pid, signal.SIGKILL)
                    time.sleep(0.5)
                except ProcessLookupError:
                    pass  # Process already terminated

            except (ProcessLookupError, PermissionError) as e:
                print(f"   Could not kill process {pid}: {e}")
                continue

        # Verify port is free
        time.sleep(1)
        remaining = self.find_processes_on_port(port)
        if remaining:
            print(f"⚠️  Warning: {len(remaining)} process(es) still running on port {port}")
            return False
        else:
            print(f"✅ Port {port} is now free")
            return True

    def is_port_available(self, port):
        """Check if a port is available"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result != 0
        except Exception:
            return False

    def find_available_port(self, start_port=8501, max_attempts=10):
        """Find the next available port starting from start_port"""
        for i in range(max_attempts):
            port = start_port + i
            if self.is_port_available(port):
                return port
        return None

    def setup_database(self):
        """Ensure database is set up"""
        db_path = Path('data/rms.db')

        if not db_path.exists():
            print("🔧 Database not found. Setting up...")
            try:
                result = subprocess.run([sys.executable, 'setup_database.py'],
                                      capture_output=True, text=True, check=True)
                print("✅ Database setup completed")
                return True
            except subprocess.CalledProcessError as e:
                print(f"❌ Database setup failed: {e}")
                print(f"Error output: {e.stderr}")
                return False
        else:
            print("✅ Database found")
            return True

    def install_dependencies(self):
        """Install required dependencies"""
        print("📦 Checking dependencies...")

        required_packages = ['streamlit', 'pandas', 'numpy', 'plotly']
        missing_packages = []

        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            print(f"📥 Installing missing packages: {', '.join(missing_packages)}")
            try:
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', '--quiet'
                ] + missing_packages, check=True)
                print("✅ Dependencies installed")
                return True
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install dependencies: {e}")
                return False
        else:
            print("✅ All dependencies available")
            return True

    def launch_streamlit(self, port):
        """Launch Streamlit application on specified port"""
        print(f"🚀 Starting RMS on port {port}...")

        # Choose the appropriate app file
        app_file = 'simple_app.py' if Path('simple_app.py').exists() else 'app.py'

        if not Path(app_file).exists():
            print(f"❌ Application file {app_file} not found")
            return None

        try:
            # Start Streamlit process
            process = subprocess.Popen([
                sys.executable, '-m', 'streamlit', 'run', app_file,
                '--server.port', str(port),
                '--server.address', 'localhost',
                '--server.headless', 'true',
                '--browser.gatherUsageStats', 'false'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # Wait a moment for startup
            time.sleep(3)

            # Check if process is still running
            if process.poll() is None:
                print(f"✅ RMS launched successfully!")
                print(f"🌐 Access URL: http://localhost:{port}")
                print(f"📊 Dashboard: Grand Millennium Dubai RMS")
                return process
            else:
                stdout, stderr = process.communicate()
                print(f"❌ Streamlit failed to start")
                print(f"Error: {stderr.decode()}")
                return None

        except Exception as e:
            print(f"❌ Failed to launch Streamlit: {e}")
            return None

    def cleanup_on_exit(self):
        """Clean up processes on exit"""
        for process in self.streamlit_processes:
            if process and process.poll() is None:
                print(f"🧹 Cleaning up process {process.pid}...")
                process.terminate()
                time.sleep(1)
                if process.poll() is None:
                    process.kill()

    def run(self):
        """Main launcher logic"""
        print("=" * 60)
        print("🏨 GRAND MILLENNIUM DUBAI - RMS SMART LAUNCHER")
        print("=" * 60)
        print()

        # Setup signal handler for cleanup
        signal.signal(signal.SIGINT, lambda s, f: self.cleanup_and_exit())
        signal.signal(signal.SIGTERM, lambda s, f: self.cleanup_and_exit())

        # Step 1: Setup database
        if not self.setup_database():
            print("❌ Database setup failed. Exiting.")
            return 1

        # Step 2: Install dependencies
        if not self.install_dependencies():
            print("❌ Dependency installation failed. Exiting.")
            return 1

        # Step 3: Handle port management
        print("\n🔍 Checking ports...")

        # Kill processes on default Streamlit ports
        for port in self.default_ports[:3]:  # Check first 3 ports
            if not self.is_port_available(port):
                print(f"⚠️  Port {port} is busy")
                self.kill_port(port)

        # Step 4: Find available port
        available_port = self.find_available_port()
        if not available_port:
            print("❌ No available ports found in range 8501-8510")
            return 1

        print(f"✅ Using port {available_port}")
        print()

        # Step 5: Launch application
        process = self.launch_streamlit(available_port)
        if not process:
            return 1

        self.streamlit_processes.append(process)

        print()
        print("=" * 60)
        print("🎉 RMS IS NOW RUNNING!")
        print("=" * 60)
        print(f"🌐 URL: http://localhost:{available_port}")
        print("🏨 Hotel: Grand Millennium Dubai (339 rooms)")
        print("💰 Target ADR: 319 AED")
        print("📊 Features: Dynamic Pricing | Channel Management | Competitor Analysis")
        print()
        print("Press Ctrl+C to stop the application")
        print("=" * 60)

        # Wait for process or user interrupt
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            self.cleanup_on_exit()

        return 0

    def cleanup_and_exit(self):
        """Clean up and exit gracefully"""
        print("\n🧹 Cleaning up...")
        self.cleanup_on_exit()
        sys.exit(0)

def main():
    """Entry point"""
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    launcher = RMSLauncher()
    return launcher.run()

if __name__ == "__main__":
    sys.exit(main())