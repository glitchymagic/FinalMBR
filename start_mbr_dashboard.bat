@echo off
rem MBR Dashboard Launcher Script for Windows
rem This script launches the MBR Dashboard application and opens it in the default browser

echo ========================================================
echo MBR Dashboard - ESS Compliance Analysis
echo Developed by Jonathan J and Nitin G
echo ========================================================
echo.
echo Starting MBR Dashboard server...
echo.

rem Start the dashboard application
if exist "MBR_Dashboard.exe" (
    rem Open browser after a short delay to ensure the server is running
    start /b cmd /c "timeout /t 2 /nobreak > nul && start http://localhost:8080"
    
    rem Run the dashboard application
    MBR_Dashboard.exe
) else (
    echo ERROR: MBR_Dashboard.exe not found!
    echo Please make sure you're running this script from the correct directory.
    pause
    exit /b 1
)

pause 