# MBR Dashboard Executable Build Guide

## Overview
The MBR Dashboard has been packaged as a standalone executable that can run on any macOS or Windows machine without requiring Python installation. This guide explains the build process and distribution method.

## What We Created

### 1. **main.py** - Launcher Script
- Automatically finds an available port
- Starts the Flask server
- Opens the dashboard in the default browser
- Handles graceful shutdown

### 2. **mbr_dashboard.spec** - PyInstaller Configuration
- Specifies which files to include in the build
- Bundles all Excel data files
- Includes all HTML templates
- Excludes unnecessary libraries to reduce size

### 3. **build_executable.py** - Build Automation
- Cleans previous builds
- Runs PyInstaller with the spec file
- Creates README for end users
- Reports build status

### 4. **create_installer.py** - Distribution Package
- Creates a dated zip file
- Includes platform-specific launchers
- Provides clear instructions

## Build Process

### Step 1: Install PyInstaller
```bash
pip install pyinstaller
```

### Step 2: Build the Executable
```bash
python build_executable.py
```

This creates:
- `dist/MBR_Dashboard/` - The distribution folder
- `dist/MBR_Dashboard/MBR_Dashboard` - The executable
- `dist/MBR_Dashboard/README.txt` - User instructions

### Step 3: Create Installer Package
```bash
python create_installer.py
```

This creates:
- `MBR_Dashboard_Installer_YYYYMMDD.zip` - Ready for distribution

## Distribution

### For Your Manager:
1. Send the `MBR_Dashboard_Installer_YYYYMMDD.zip` file
2. They unzip it to any location
3. **On Mac**: Double-click `run_dashboard.command`
4. **On Windows**: Double-click `run_dashboard.bat`
5. The dashboard opens automatically in their browser

### Features:
- ✅ No Python installation required
- ✅ All data files included
- ✅ Automatic browser opening
- ✅ Port conflict resolution
- ✅ Clean shutdown handling
- ✅ Cross-platform support

## Technical Details

### Included Files:
- Flask application (`app.py`)
- HTML templates
- Excel data files:
  - `Combined_Incidents_Report_Feb_to_June_2025.xlsx`
  - `Pre-TSQ Data-FebTOJune2025.xlsx`
  - `Regions-Groups.xlsx`

### Security:
- Source code is compiled and bundled
- Data files are embedded in the package
- Runs locally (no internet required)
- Uses random port to avoid conflicts

### File Size:
- Executable package: ~170 MB
- Includes Python runtime and all dependencies
- Compressed for distribution

## Troubleshooting

### If the dashboard doesn't open:
1. Check the terminal/console window for the port number
2. Manually navigate to `http://127.0.0.1:[PORT]`
3. Ensure no firewall is blocking local connections

### If you get a security warning:
- **Mac**: Right-click → Open → Open Anyway
- **Windows**: Properties → Unblock → Apply

### To rebuild after changes:
1. Make your code changes
2. Run `python build_executable.py`
3. Run `python create_installer.py`
4. Distribute the new zip file

## Alternative: Electron-based Solution

If you want a more native desktop app experience, you could:
1. Create an Electron wrapper around the Flask app
2. Bundle everything as a `.app` (Mac) or `.exe` (Windows)
3. Add desktop app features like system tray, notifications

However, the current PyInstaller solution is simpler and works well for this use case.

---
**Developed by Jonathan J and Nitin G** 