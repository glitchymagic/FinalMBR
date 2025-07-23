#!/usr/bin/env python3
"""
Simplified build script for MBR Dashboard executable
"""

import os
import sys
import shutil
import subprocess
import platform
from datetime import datetime

def clean_build_directories():
    """Remove old build directories"""
    dirs_to_remove = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            print(f"🧹 Removing {dir_name}...")
            shutil.rmtree(dir_name)

def build_executable():
    """Build the executable using PyInstaller"""
    print("\n" + "=" * 60)
    print("MBR Dashboard - Build Script")
    print("=" * 60)
    
    # Clean old builds
    clean_build_directories()
    
    # Determine platform
    current_platform = platform.system()
    print(f"Building for: {current_platform}")
    
    # Choose the appropriate spec file
    if current_platform == "Windows":
        spec_file = "mbr_dashboard_windows.spec"
        output_dir = "dist/MBR_Dashboard_Windows"
    else:
        spec_file = "mbr_dashboard_protected.spec"
        output_dir = "dist/MBR_Dashboard"
    
    # Run PyInstaller
    print(f"\n📦 Building executable using {spec_file}...")
    cmd = [sys.executable, '-m', 'PyInstaller', spec_file, '--clean']
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\n✅ Build successful!")
            
            # Copy startup scripts
            if current_platform == "Windows":
                shutil.copy("start_mbr_dashboard.bat", f"{output_dir}/Start_Dashboard.bat")
                print(f"📄 Copied startup script to {output_dir}/Start_Dashboard.bat")
            else:
                shutil.copy("start_mbr_dashboard.sh", f"{output_dir}/Start_Dashboard.sh")
                os.chmod(f"{output_dir}/Start_Dashboard.sh", 0o755)
                print(f"📄 Copied startup script to {output_dir}/Start_Dashboard.sh")
            
            # Create README
            readme_content = f"""
MBR Dashboard - ESS Compliance Analysis
======================================

Developed by Jonathan J and Nitin G
Built on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

How to Run:
-----------
1. Double-click 'Start_Dashboard{"" if current_platform == "Windows" else ".sh"}'
2. The dashboard will automatically open in your default browser
3. To stop the server, close the terminal window or press Ctrl+C

Requirements:
-------------
- No installation required
- Works on {"Windows" if current_platform == "Windows" else "macOS"}
- Internet browser (Chrome, Firefox, Safari, Edge)

Troubleshooting:
----------------
- If the dashboard doesn't open automatically, navigate to:
  http://127.0.0.1:8080
- Make sure no other application is using port 8080
- Check firewall settings if you encounter connection issues

"""
            
            with open(f'{output_dir}/README.txt', 'w') as f:
                f.write(readme_content)
            
            print(f"\n📦 Package ready for distribution in: {output_dir}/")
            print("\nTo run the dashboard:")
            if current_platform == "Windows":
                print(f"  1. Navigate to {output_dir}")
                print(f"  2. Double-click Start_Dashboard.bat")
            else:
                print(f"  1. Navigate to {output_dir}")
                print(f"  2. Run ./Start_Dashboard.sh")
            
        else:
            print("\n❌ Build failed!")
            print(f"Error: {result.stderr}")
            return 1
            
    except Exception as e:
        print(f"\n❌ Build error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(build_executable()) 