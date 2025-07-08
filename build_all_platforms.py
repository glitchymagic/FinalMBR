#!/usr/bin/env python3
"""
Multi-platform build script for MBR Dashboard executable
Builds executable packages for macOS and Windows distribution
"""

import os
import sys
import shutil
import subprocess
import platform
import zipfile
from datetime import datetime

def clean_build_directories():
    """Remove old build directories"""
    dirs_to_remove = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            print(f"🧹 Removing {dir_name}...")
            shutil.rmtree(dir_name)

def create_build_info():
    """Create build information file"""
    build_info = f"""MBR Dashboard Build Information
===============================

Build Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Build Platform: {platform.system()} {platform.release()}
Python Version: {sys.version}
Architecture: {platform.architecture()[0]}

Developers: Jonathan J and Nitin G

Files Included:
- MBR_Dashboard executable
- Combined_Incidents_Report_Feb_to_June_2025.xlsx
- Pre-TSQ Data-FebTOJune2025.xlsx  
- Regions-Groups.xlsx
- Templates (dashboard.html, consultations.html)
- All required Python libraries and dependencies

Data Security:
- Source code is compiled and obfuscated
- No source code files are included in distribution
- All data processing happens locally
- No external network connections required
"""
    return build_info

def build_executable(platform_name="current"):
    """Build the executable using PyInstaller"""
    print(f"🔨 Building MBR Dashboard executable for {platform_name}...")
    
    # Clean old builds
    clean_build_directories()
    
    # Choose the appropriate spec file
    if platform_name.lower() == "windows":
        spec_file = "mbr_dashboard_windows.spec"
    else:
        spec_file = "mbr_dashboard_protected.spec"
    
    # Run PyInstaller
    cmd = [sys.executable, '-m', 'PyInstaller', spec_file, '--clean', '--noconfirm']
    
    try:
        print(f"📦 Running PyInstaller with {spec_file}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\n✅ Build successful!")
            
            # Determine output directory
            if platform_name.lower() == "windows":
                output_dir = "dist/MBR_Dashboard_Windows"
            else:
                output_dir = "dist/MBR_Dashboard"
            
            print(f"📍 Executable location: {output_dir}/")
            
            # Create build info file
            build_info_content = create_build_info()
            with open(f'{output_dir}/BUILD_INFO.txt', 'w') as f:
                f.write(build_info_content)
            
            # Create startup script for easier execution
            if platform.system() == "Windows" or platform_name.lower() == "windows":
                startup_script = f"""@echo off
echo MBR Dashboard - ESS Compliance Analysis
echo Developed by Jonathan J and Nitin G
echo.
echo Starting dashboard server...
echo.
MBR_Dashboard.exe
pause
"""
                with open(f'{output_dir}/Start_Dashboard.bat', 'w') as f:
                    f.write(startup_script)
            else:
                startup_script = f"""#!/bin/bash
echo "MBR Dashboard - ESS Compliance Analysis"
echo "Developed by Jonathan J and Nitin G"
echo ""
echo "Starting dashboard server..."
echo ""
./MBR_Dashboard
"""
                with open(f'{output_dir}/Start_Dashboard.sh', 'w') as f:
                    f.write(startup_script)
                os.chmod(f'{output_dir}/Start_Dashboard.sh', 0o755)
            
            # Calculate size
            size_cmd = ['du', '-sh', output_dir] if platform.system() != "Windows" else ['dir', output_dir]
            try:
                size_result = subprocess.run(size_cmd, capture_output=True, text=True)
                if size_result.returncode == 0:
                    if platform.system() != "Windows":
                        size = size_result.stdout.split()[0]
                        print(f"📏 Package size: {size}")
                    else:
                        print("📏 Package size: Check directory properties")
            except:
                print("📏 Package size: Unable to determine")
            
            print(f"\n📦 Package ready for distribution in: {output_dir}/")
            return True
            
        else:
            print("\n❌ Build failed!")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"\n❌ Build error: {e}")
        return False

def create_distribution_package():
    """Create a distributable package"""
    print("\n📦 Creating distribution package...")
    
    # Check if build was successful
    dist_dirs = []
    if os.path.exists("dist/MBR_Dashboard"):
        dist_dirs.append(("dist/MBR_Dashboard", "MBR_Dashboard_macOS"))
    if os.path.exists("dist/MBR_Dashboard_Windows"):
        dist_dirs.append(("dist/MBR_Dashboard_Windows", "MBR_Dashboard_Windows"))
    
    if not dist_dirs:
        print("❌ No built distributions found!")
        return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for dist_dir, platform_name in dist_dirs:
        zip_name = f"MBR_Dashboard_{platform_name}_{timestamp}.zip"
        
        print(f"🗜️  Creating {zip_name}...")
        
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
            for root, dirs, files in os.walk(dist_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, dist_dir)
                    zipf.write(file_path, arcname)
        
        # Calculate zip size
        zip_size = os.path.getsize(zip_name) / (1024 * 1024)  # MB
        print(f"✅ Created {zip_name} ({zip_size:.1f} MB)")
    
    return True

def verify_requirements():
    """Verify all required files are present"""
    required_files = [
        'main.py',
        'app.py',
        'MTTR.py',
        'Combined_Incidents_Report_Feb_to_June_2025.xlsx',
        'Pre-TSQ Data-FebTOJune2025.xlsx',
        'Regions-Groups.xlsx',
        'templates/dashboard.html',
        'templates/consultations.html'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ All required files present")
    return True

def main():
    """Main entry point for the build script"""
    print("=" * 60)
    print("MBR Dashboard - Multi-Platform Build Script")
    print("Developed by Jonathan J and Nitin G")
    print("=" * 60)
    
    # Verify requirements
    if not verify_requirements():
        print("\n❌ Build cannot proceed due to missing files")
        return 1
    
    # Build for current platform
    current_platform = platform.system()
    if not build_executable(current_platform):
        return 1
    
    # Ask if user wants to create distribution package
    try:
        create_dist = input("\n📦 Create distribution package (zip)? (y/N): ").lower().strip()
        if create_dist in ['y', 'yes']:
            create_distribution_package()
    except KeyboardInterrupt:
        print("\n\n👋 Build completed without packaging")
    
    print("\n🎉 Build process complete!")
    print("\nNext steps:")
    print("1. Test the executable in dist/ directory")
    print("2. Distribute the package to end users")
    print("3. Include README.txt with distribution")
    
    return 0

if __name__ == '__main__':
    sys.exit(main()) 