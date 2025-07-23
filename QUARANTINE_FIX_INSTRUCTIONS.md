# Tech Spot FY26 Report - macOS "Damaged" Error Fix

## Problem
When you download and try to open "Tech Spot FY26 Report.app", macOS shows an error saying the app is "damaged and can't be opened" and suggests moving it to Trash.

## Why This Happens
This is **NOT** because the app is actually damaged. This is macOS Gatekeeper's security feature that blocks unsigned applications downloaded from the internet. The app is completely safe and functional.

## Solutions (Choose One)

### Solution 1: Automatic Fix Script (Recommended)
The easiest way to fix this issue:

1. **Extract the zip file** completely
2. **Open Terminal** (Applications > Utilities > Terminal)
3. **Navigate to the folder** containing the app:
   - Type `cd ` (with a space after cd)
   - Drag the folder from Finder into Terminal
   - Press Enter
4. **Run the fix script**:
   ```bash
   ./fix_macos_quarantine.sh
   ```
5. **Launch the app** by double-clicking "Tech Spot FY26 Report.app"

### Solution 2: Right-Click Method
If you prefer not to use Terminal:

1. **Right-click** on "Tech Spot FY26 Report.app"
2. Select **"Open"** from the context menu
3. Click **"Open"** when macOS asks for confirmation
4. The app will launch normally

### Solution 3: Manual Terminal Command
For advanced users:

1. Open Terminal
2. Navigate to the app folder
3. Run this command:
   ```bash
   xattr -d com.apple.quarantine "Tech Spot FY26 Report.app"
   ```
4. Double-click the app to launch

## After First Launch
Once you successfully open the app using any of these methods, macOS will remember it's safe and you can launch it normally in the future by double-clicking.

## What the App Does
- Launches automatically in your web browser
- Runs on port 8080 (http://localhost:8080)
- Contains all your FY26 consultation and incident data
- Works completely offline - no internet connection needed
- All data is embedded within the application

## Troubleshooting

### If the fix script won't run:
```bash
chmod +x fix_macos_quarantine.sh
./fix_macos_quarantine.sh
```

### If you see "command not found":
Make sure you're in the correct folder containing the app and script.

### If the app still won't open:
Try Solution 2 (right-click method) as a backup.

## Security Note
This application is completely safe. It was built using PyInstaller, a legitimate Python packaging tool. The "damaged" warning is purely due to the app not being signed with an Apple Developer Certificate, which is normal for internal business applications.

## Need Help?
If none of these solutions work, contact your IT support team or the person who provided this application.

---

**File Contents:**
- `Tech Spot FY26 Report.app` - The main application
- `fix_macos_quarantine.sh` - Automatic fix script
- `QUICK_FIX_README.txt` - Quick reference guide
- This file - Detailed instructions 