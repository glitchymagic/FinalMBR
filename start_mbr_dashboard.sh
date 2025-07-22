#!/bin/bash
# MBR Dashboard Launcher Script
# This script launches the MBR Dashboard application and opens it in the default browser

echo "========================================================"
echo "MBR Dashboard - ESS Compliance Analysis"
echo "Developed by Jonathan J and Nitin G"
echo "========================================================"
echo ""
echo "Starting MBR Dashboard server..."
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Start the dashboard application
if [ -f "./MBR_Dashboard" ]; then
    # Open browser after a short delay to ensure the server is running
    (sleep 2 && open http://localhost:8080) &
    
    # Run the dashboard application
    ./MBR_Dashboard
else
    echo "ERROR: MBR_Dashboard executable not found!"
    echo "Please make sure you're running this script from the correct directory."
    exit 1
fi 