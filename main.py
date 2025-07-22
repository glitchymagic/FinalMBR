#!/usr/bin/env python3
"""
MBR Dashboard Launcher
Developed by Jonathan J and Nitin G
"""

import os
import sys
import time
import threading
import webbrowser
import socket
import signal
from contextlib import closing

# Add the current directory to the Python path
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app path
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

os.chdir(application_path)
sys.path.insert(0, application_path)

# Import the Flask app and load data
from app import app, load_data

# Ensure data is loaded
if not load_data():
    print("ERROR: Failed to load data. Please check the Excel files.")
    sys.exit(1)

def find_free_port():
    """Find a free port to run the server on"""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

def wait_for_server(port, timeout=10):
    """Wait for the Flask server to start"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=1):
                return True
        except (socket.error, ConnectionRefusedError):
            time.sleep(0.1)
    return False

def open_browser(port):
    """Open the default browser to the dashboard"""
    time.sleep(1)  # Give the server a moment to fully initialize
    if wait_for_server(port):
        webbrowser.open(f'http://127.0.0.1:{port}')
    else:
        print("Warning: Server took too long to start")

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    print("\nShutting down MBR Dashboard...")
    sys.exit(0)

def main():
    """Main entry point for the application"""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("Tech Spot FY26 Report - ESS Compliance Analysis")
    print("Developed by Jonathan J and Nitin G")
    print("=" * 60)
    print("\nStarting dashboard server...")
    
    # Find a free port
    port = find_free_port()
    print(f"Using port: {port}")
    
    # Start browser opener in a separate thread
    browser_thread = threading.Thread(target=open_browser, args=(port,))
    browser_thread.daemon = True
    browser_thread.start()
    
    print(f"\nDashboard will open automatically in your browser")
    print(f"If it doesn't, navigate to: http://127.0.0.1:{port}")
    print("\nPress Ctrl+C to stop the server")
    print("-" * 60)
    
    # Run the Flask app
    try:
        app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"\nError: {e}")
        print("Press Enter to exit...")
        input()

if __name__ == '__main__':
    main() 