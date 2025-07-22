#!/usr/bin/env python3
"""
Create installer package for MBR Dashboard
"""

import os
import sys
import shutil
import zipfile
from datetime import datetime

def create_installer():
    """Create a zip file containing the executable and all necessary files"""
    
    if not os.path.exists('dist/MBR_Dashboard'):
        print("❌ Error: No build found. Run build_executable.py first.")
        return 1
    
    # Create installer filename with date
    date_str = datetime.now().strftime('%Y%m%d')
    installer_name = f"MBR_Dashboard_Installer_{date_str}"
    
    print(f"Creating installer package: {installer_name}.zip")
    
    # Create a temporary directory for the installer
    if os.path.exists(installer_name):
        shutil.rmtree(installer_name)
    
    # Copy the distribution folder
    shutil.copytree('dist/MBR_Dashboard', installer_name)
    
    # Create a simple run script for macOS
    run_script = f"""#!/bin/bash
cd "$(dirname "$0")"
./MBR_Dashboard
"""
    
    with open(f'{installer_name}/run_dashboard.command', 'w') as f:
        f.write(run_script)
    
    # Make it executable
    os.chmod(f'{installer_name}/run_dashboard.command', 0o755)
    
    # Create a batch file for Windows
    run_batch = """@echo off
cd /d "%~dp0"
MBR_Dashboard.exe
pause
"""
    
    with open(f'{installer_name}/run_dashboard.bat', 'w') as f:
        f.write(run_batch)
    
    # Create the zip file
    with zipfile.ZipFile(f'{installer_name}.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(installer_name):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(installer_name))
                zipf.write(file_path, arcname)
    
    # Clean up temporary directory
    shutil.rmtree(installer_name)
    
    # Get file size
    size_mb = os.path.getsize(f'{installer_name}.zip') / (1024 * 1024)
    
    print(f"\n✅ Installer created successfully!")
    print(f"📦 File: {installer_name}.zip ({size_mb:.1f} MB)")
    print(f"\n📋 Distribution instructions:")
    print(f"1. Send '{installer_name}.zip' to your manager")
    print(f"2. They should unzip the file")
    print(f"3. On Mac: Double-click 'run_dashboard.command'")
    print(f"4. On Windows: Double-click 'run_dashboard.bat'")
    print(f"5. Or directly run 'MBR_Dashboard' executable")
    
    return 0

if __name__ == '__main__':
    sys.exit(create_installer()) 