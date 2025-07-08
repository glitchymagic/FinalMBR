#!/bin/bash

# Fix macOS Quarantine Issue for Tech Spot FY26 Report
# This script removes the quarantine attribute that causes the "damaged" error

echo "=================================================="
echo "Tech Spot FY26 Report - macOS Quarantine Fix"
echo "=================================================="
echo ""

# Check if the app exists
if [ ! -d "Tech Spot FY26 Report.app" ]; then
    echo "❌ Error: 'Tech Spot FY26 Report.app' not found in current directory"
    echo "Please run this script from the folder containing the app"
    exit 1
fi

echo "🔍 Checking current quarantine status..."
xattr -l "Tech Spot FY26 Report.app"

echo ""
echo "🔧 Removing quarantine attributes..."

# Remove quarantine attribute
xattr -d com.apple.quarantine "Tech Spot FY26 Report.app" 2>/dev/null || echo "No quarantine attribute found (this is normal)"

# Remove other potential blocking attributes
xattr -d com.apple.quarantine "Tech Spot FY26 Report.app/Contents/MacOS/Tech Spot FY26 Report" 2>/dev/null || true

# Make executable
chmod +x "Tech Spot FY26 Report.app/Contents/MacOS/Tech Spot FY26 Report"

echo ""
echo "✅ Quarantine removal complete!"
echo ""
echo "🔍 Verifying fix..."
xattr -l "Tech Spot FY26 Report.app"

echo ""
echo "🎉 The app should now open without the 'damaged' error!"
echo ""
echo "To run the application:"
echo "1. Double-click 'Tech Spot FY26 Report.app'"
echo "2. If you still see a warning, right-click and select 'Open'"
echo "3. Click 'Open' in the security dialog"
echo ""
echo "==================================================" 