#!/usr/bin/env python3
"""
Simple build script for Tech Spot FY26 Report
Uses existing build infrastructure with updated branding
"""

import os
import sys
import subprocess
import platform

def main():
    """Build Tech Spot FY26 Report executable"""
    print("=" * 60)
    print("Tech Spot FY26 Report - Build System")
    print("=" * 60)
    
    # Check if we're on macOS
    if platform.system() == "Darwin":
        print("🍎 Building for macOS...")
        spec_file = "tech_spot_fy26_macos.spec"
    else:
        print("🪟 Building for Windows...")
        spec_file = "tech_spot_fy26_windows.spec"
    
    # Check if spec file exists
    if not os.path.exists(spec_file):
        print(f"❌ Spec file {spec_file} not found!")
        print("Please ensure the spec files are in the current directory.")
        return False
    
    # Run PyInstaller
    print(f"📦 Running PyInstaller with {spec_file}...")
    cmd = [sys.executable, '-m', 'PyInstaller', spec_file, '--clean', '--noconfirm']
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Build successful!")
            
            if platform.system() == "Darwin":
                print("📍 Executable: dist/Tech Spot FY26 Report.app")
                print("📋 To run: Double-click the .app file")
            else:
                print("📍 Executable: dist/Tech Spot FY26 Report.exe")
                print("📋 To run: Double-click the .exe file")
            
            print("\n🎉 Tech Spot FY26 Report is ready!")
            print("📦 The executable includes all data files and dependencies.")
            print("🚀 Share the 'dist' folder with your director.")
            
            return True
        else:
            print("❌ Build failed!")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False

if __name__ == '__main__':
    main() 