@echo off
REM MBR Dashboard Launcher Script for Windows
REM This script launches the MBR Dashboard application and opens it in the default browser

echo ========================================================
echo MBR Dashboard - ESS Compliance Analysis
echo Developed by Jonathan J and Nitin G
echo ========================================================
echo.
echo Starting MBR Dashboard server...
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Change to the script directory
cd /d "%SCRIPT_DIR%"

REM Start the dashboard application
if exist "MBR_Dashboard.exe" (
    REM Open browser after a short delay to ensure the server is running
    timeout /t 3 /nobreak >nul && start http://localhost:8080
    
    REM Run the dashboard application
    MBR_Dashboard.exe
) else (
    echo ERROR: MBR_Dashboard.exe not found!
    echo Please make sure you're running this script from the correct directory.
    pause
    exit /b 1
)