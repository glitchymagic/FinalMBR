#!/usr/bin/env python3
"""
Comprehensive fix for all timezone issues in the MBR Dashboard
"""

import os
import sys
import shutil
import re
from datetime import datetime

def backup_file(file_path):
    """Create a backup of the original file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Created backup: {backup_path}")
    return backup_path

def fix_specific_functions(content):
    """Fix timezone issues in specific functions"""
    # Find and fix the api_sla_breach_incidents function
    pattern1 = r"days_ago = \(datetime\.now\(\) - incident\['Created'\]\)\.days"
    replacement1 = r"days_ago = (datetime.now(tz=incident['Created'].tzinfo) - incident['Created']).days"
    content = content.replace(pattern1, replacement1)
    
    # Find and fix the api_team_drill_down function
    pattern2 = r"days_ago = \(datetime\.now\(\) - row\['Created'\]\)\.days"
    replacement2 = r"days_ago = (datetime.now(tz=row['Created'].tzinfo) - row['Created']).days"
    content = content.replace(pattern2, replacement2)
    
    # Find and fix other datetime calculations
    pattern3 = r"days_ago = \(datetime\.now\(\) - incident\['Created'\]\)\.days"
    replacement3 = r"days_ago = (datetime.now(tz=incident['Created'].tzinfo) - incident['Created']).days"
    content = content.replace(pattern3, replacement3)
    
    return content

def add_timezone_utilities(content):
    """Add timezone utility functions to the app"""
    # Find a good insertion point - after the imports
    insertion_point = content.find("app = Flask(__name__)")
    
    if insertion_point == -1:
        print("❌ Could not find insertion point for timezone utilities")
        return content
    
    # Define the utility functions
    utilities = """
# Timezone utilities
def ensure_tz_aware(dt, default_tz='UTC'):
    '''Ensure a datetime object has timezone information'''
    if dt is None:
        return None
    
    if isinstance(dt, pd.Timestamp):
        if dt.tzinfo is None:
            return dt.tz_localize(default_tz)
        return dt
    
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            from pytz import timezone
            return timezone(default_tz).localize(dt)
        return dt
    
    return dt

def now_with_tz(tz=None):
    '''Get current time with timezone'''
    now = datetime.now()
    if tz is None:
        return now.replace(tzinfo=pd.Timestamp.now().tzinfo)
    else:
        from pytz import timezone
        return timezone(tz).localize(now)

"""
    
    # Insert the utility functions before the app definition
    updated_content = content[:insertion_point] + utilities + content[insertion_point:]
    
    return updated_content

def fix_datetime_now_calls(content):
    """Fix all datetime.now() calls to use timezone-aware version"""
    # Replace direct datetime.now() calls with now_with_tz()
    pattern = r"datetime\.now\(\)"
    replacement = r"now_with_tz()"
    
    return content.replace(pattern, replacement)

def fix_timezone_comparisons(content):
    """Fix timezone comparisons in the code"""
    # Find date comparisons and ensure they use the same timezone
    patterns = [
        # Pattern 1: Filtering by date ranges
        (r"(\(filtered_df\['Created'\] >= )([^)]+)( & filtered_df\['Created'\] <= )([^)]+)(\))",
         r"\1ensure_tz_aware(\2)\3ensure_tz_aware(\4)\5"),
        
        # Pattern 2: Date comparisons in conditionals
        (r"(if )([a-zA-Z0-9_\[\]\'\.]+)( [<>=]+ )([a-zA-Z0-9_\[\]\'\.]+)(:)",
         r"\1ensure_tz_aware(\2)\3ensure_tz_aware(\4)\5")
    ]
    
    updated_content = content
    for pattern, replacement in patterns:
        updated_content = re.sub(pattern, replacement, updated_content)
    
    return updated_content

def main():
    """Main function to apply all fixes"""
    app_py_path = 'app.py'
    
    if not os.path.exists(app_py_path):
        print(f"❌ Error: {app_py_path} not found!")
        return 1
    
    # Create backup
    backup_path = backup_file(app_py_path)
    
    # Read the content
    with open(app_py_path, 'r') as f:
        content = f.read()
    
    # Apply fixes
    print("🔧 Applying comprehensive timezone fixes...")
    
    # Add timezone utilities
    content = add_timezone_utilities(content)
    print("✅ Added timezone utility functions")
    
    # Fix specific functions with known issues
    content = fix_specific_functions(content)
    print("✅ Fixed timezone issues in specific functions")
    
    # Fix datetime.now() calls
    content = fix_datetime_now_calls(content)
    print("✅ Fixed datetime.now() calls to use timezone-aware version")
    
    # Fix timezone comparisons
    content = fix_timezone_comparisons(content)
    print("✅ Fixed timezone comparisons in date filtering")
    
    # Write the updated content
    with open(app_py_path, 'w') as f:
        f.write(content)
    
    print("\n✅ Successfully applied all timezone fixes!")
    print("🚀 Restart the dashboard to apply the changes.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
