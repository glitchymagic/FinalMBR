#!/usr/bin/env python3
"""
Build script for MBR Dashboard executable
"""

import os
import sys
import shutil
import subprocess

def clean_build_directories():
    """Remove old build directories"""
    dirs_to_remove = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            print(f"Removing {dir_name}...")
            shutil.rmtree(dir_name)

def build_executable():
    """Build the executable using PyInstaller"""
    print("Building MBR Dashboard executable...")
    
    # Clean old builds
    clean_build_directories()
    
    # Run PyInstaller
    cmd = [sys.executable, '-m', 'PyInstaller', 'mbr_dashboard.spec', '--clean']
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\n✅ Build successful!")
            print(f"\nExecutable location: dist/MBR_Dashboard/MBR_Dashboard")
            
            # Create a simple readme
            readme_content = """
MBR Dashboard - ESS Compliance Analysis
======================================

Developed by Jonathan J and Nitin G

How to Run:
-----------
1. Double-click 'MBR_Dashboard' (or 'MBR_Dashboard.exe' on Windows)
2. The dashboard will automatically open in your default browser
3. To stop the server, close the terminal window or press Ctrl+C

Requirements:
-------------
- No installation required
- Works on macOS and Windows
- Internet browser (Chrome, Firefox, Safari, Edge)

Troubleshooting:
----------------
- If the dashboard doesn't open automatically, navigate to:
  http://127.0.0.1:8080 (or the port shown in the terminal)
- Make sure no other application is using the same port
- Check firewall settings if you encounter connection issues

"""
            
            with open('dist/MBR_Dashboard/README.txt', 'w') as f:
                f.write(readme_content)
            
            print("\n📦 Package ready for distribution in: dist/MBR_Dashboard/")
            
        else:
            print("\n❌ Build failed!")
            print(f"Error: {result.stderr}")
            
    except Exception as e:
        print(f"\n❌ Build error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(build_executable()) 