#!/usr/bin/env python3
"""
Build script for Tech Spot FY26 Report
Creates standalone executables for macOS and Windows
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
    build_info = f"""Tech Spot FY26 Report - Build Information
===============================================

Application: Tech Spot FY26 Report
Version: 1.0.0
Build Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Build Platform: {platform.system()} {platform.release()}
Python Version: {sys.version}
Architecture: {platform.architecture()[0]}

Description:
ESS Compliance Analysis Dashboard for FY26 reporting period.
Comprehensive incident management and consultation analytics.

Files Included:
- Tech Spot FY26 Report executable
- Combined_Incidents_Report_Feb_to_June_2025.xlsx
- Pre-TSQ Data-FebTOJune2025.xlsx  
- Regions-Groups.xlsx
- Templates (dashboard.html, consultations.html)
- All required Python libraries and dependencies

Features:
- Incident tracking and MTTR analysis
- SLA compliance monitoring
- Consultation analytics and technician performance
- Interactive charts and drill-down capabilities
- Real-time filtering and data visualization

Data Security:
- Source code is compiled and obfuscated
- No source code files are included in distribution
- All data processing happens locally
- No external network connections required

Usage:
1. Double-click the executable to launch
2. Dashboard will open automatically in your default browser
3. Use filters to analyze specific time periods or regions
4. Click on charts and cards for detailed drill-down analysis

System Requirements:
- macOS 10.14+ or Windows 10+
- 4GB RAM minimum, 8GB recommended
- 1GB free disk space
- Modern web browser (Chrome, Firefox, Safari, Edge)

Support:
For technical support or questions, contact the development team.
"""
    return build_info

def build_executable(target_platform="macos"):
    """Build the executable using PyInstaller"""
    print(f"🔨 Building Tech Spot FY26 Report for {target_platform}...")
    
    # Clean old builds
    clean_build_directories()
    
    # Choose the appropriate spec file
    if target_platform.lower() == "windows":
        spec_file = "tech_spot_fy26_windows.spec"
        output_name = "Tech Spot FY26 Report"
    else:
        spec_file = "tech_spot_fy26_macos.spec"
        output_name = "Tech Spot FY26 Report"
    
    # Check if spec file exists
    if not os.path.exists(spec_file):
        print(f"❌ Spec file {spec_file} not found!")
        return False
    
    # Run PyInstaller
    cmd = [sys.executable, '-m', 'PyInstaller', spec_file, '--clean', '--noconfirm']
    
    try:
        print(f"📦 Running PyInstaller with {spec_file}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\n✅ Build successful!")
            
            # Determine output directory
            if target_platform.lower() == "windows":
                output_dir = "dist"
                exe_path = os.path.join(output_dir, f"{output_name}.exe")
            else:
                output_dir = "dist"
                app_path = os.path.join(output_dir, f"{output_name}.app")
                exe_path = app_path
            
            print(f"📍 Executable location: {exe_path}")
            
            # Create build info file
            build_info_content = create_build_info()
            info_file_path = os.path.join(output_dir, 'BUILD_INFO.txt')
            with open(info_file_path, 'w') as f:
                f.write(build_info_content)
            
            # Create startup instructions
            if target_platform.lower() == "windows":
                instructions = f"""Tech Spot FY26 Report - Windows
=====================================

To run the application:
1. Double-click "Tech Spot FY26 Report.exe"
2. The dashboard will open automatically in your default browser
3. If Windows shows a security warning, click "More info" then "Run anyway"

The application may take 10-30 seconds to start on first launch.

For best performance, ensure you have:
- At least 4GB of available RAM
- A modern web browser installed
- Windows 10 or newer

If you encounter any issues:
1. Try running as Administrator
2. Temporarily disable antivirus software
3. Check Windows Defender exclusions

Contact your IT support team if problems persist.
"""
                with open(os.path.join(output_dir, 'README.txt'), 'w') as f:
                    f.write(instructions)
            else:
                instructions = f"""Tech Spot FY26 Report - macOS
===================================

To run the application:
1. Double-click "Tech Spot FY26 Report.app"
2. The dashboard will open automatically in your default browser
3. If macOS shows a security warning, go to System Preferences > Security & Privacy and click "Open Anyway"

The application may take 10-30 seconds to start on first launch.

For best performance, ensure you have:
- At least 4GB of available RAM
- A modern web browser installed
- macOS 10.14 or newer

If you encounter any issues:
1. Try right-clicking the app and selecting "Open"
2. Check System Preferences > Security & Privacy
3. Ensure the app is not quarantined: run 'xattr -d com.apple.quarantine "Tech Spot FY26 Report.app"' in Terminal

Contact your IT support team if problems persist.
"""
                with open(os.path.join(output_dir, 'README.txt'), 'w') as f:
                    f.write(instructions)
            
            # Calculate size
            try:
                if target_platform.lower() == "windows":
                    size_result = subprocess.run(['du', '-sh', exe_path], capture_output=True, text=True)
                else:
                    size_result = subprocess.run(['du', '-sh', exe_path], capture_output=True, text=True)
                
                if size_result.returncode == 0:
                    size = size_result.stdout.split()[0]
                    print(f"📏 Package size: {size}")
                else:
                    print("📏 Package size: Unable to determine")
            except:
                print("📏 Package size: Check directory properties")
            
            print(f"\n📦 Package ready for distribution in: {output_dir}/")
            return True
            
        else:
            print("\n❌ Build failed!")
            print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"\n❌ Build error: {e}")
        return False

def create_distribution_package(target_platform="macos"):
    """Create a distributable package"""
    print(f"\n📦 Creating distribution package for {target_platform}...")
    
    # Check if build was successful
    if target_platform.lower() == "windows":
        exe_path = "dist/Tech Spot FY26 Report.exe"
        if not os.path.exists(exe_path):
            print("❌ Windows executable not found!")
            return False
    else:
        app_path = "dist/Tech Spot FY26 Report.app"
        if not os.path.exists(app_path):
            print("❌ macOS app bundle not found!")
            return False
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if target_platform.lower() == "windows":
        zip_name = f"Tech_Spot_FY26_Report_Windows_{timestamp}.zip"
        source_dir = "dist"
    else:
        zip_name = f"Tech_Spot_FY26_Report_macOS_{timestamp}.zip"
        source_dir = "dist"
    
    print(f"🗜️  Creating {zip_name}...")
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
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
    """Main build function"""
    print("=" * 60)
    print("Tech Spot FY26 Report - Build System")
    print("=" * 60)
    
    # Verify requirements
    if not verify_requirements():
        print("\n❌ Build aborted due to missing files")
        return False
    
    # Check for PyInstaller
    try:
        subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'], 
                      capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
    
    success = True
    
    # Build for current platform
    current_platform = "macos" if platform.system() == "Darwin" else "windows"
    print(f"\n🏗️  Building for {current_platform}...")
    
    if build_executable(current_platform):
        if create_distribution_package(current_platform):
            print(f"\n🎉 {current_platform.title()} build completed successfully!")
        else:
            success = False
    else:
        success = False
    
    if success:
        print("\n" + "=" * 60)
        print("✅ Build process completed successfully!")
        print("\nDistribution packages created:")
        
        # List created zip files
        for file in os.listdir('.'):
            if file.startswith('Tech_Spot_FY26_Report_') and file.endswith('.zip'):
                size = os.path.getsize(file) / (1024 * 1024)
                print(f"   📦 {file} ({size:.1f} MB)")
        
        print("\n📋 Next steps:")
        print("1. Test the executable on the target platform")
        print("2. Share the zip file with your director")
        print("3. Include the README.txt for installation instructions")
        print("\n🎯 Ready for distribution!")
    else:
        print("\n❌ Build process failed!")
        return False
    
    return True

if __name__ == '__main__':
    main() 