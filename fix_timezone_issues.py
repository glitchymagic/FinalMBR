#!/usr/bin/env python3
"""
Fix timezone issues in the MBR Dashboard
This script fixes the 'Cannot subtract tz-naive and tz-aware datetime-like objects' errors
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

def fix_api_sla_breach_incidents(content):
    """Fix timezone issues in the api_sla_breach_incidents function"""
    # Find the api_sla_breach_incidents function
    start = content.find("@app.route('/api/sla_breach_incidents')")
    if start == -1:
        print("❌ Could not find api_sla_breach_incidents function")
        return content
    
    # Find the date calculations in the function
    date_calc_pattern = r"(\s+# Calculate days ago\n\s+)days_ago = \(datetime\.now\(\) - incident\['Created'\]\)\.days"
    
    # Replace with timezone-aware version
    replacement = r"\1days_ago = (datetime.now(incident['Created'].tzinfo) - incident['Created']).days"
    
    # Apply the replacement
    updated_content = re.sub(date_calc_pattern, replacement, content)
    
    if updated_content == content:
        print("⚠️ No changes made to api_sla_breach_incidents function")
    else:
        print("✅ Fixed timezone issues in api_sla_breach_incidents function")
    
    return updated_content

def fix_api_team_drill_down(content):
    """Fix timezone issues in the api_team_drill_down function"""
    # Find the api_team_drill_down function
    start = content.find("@app.route('/api/team_drill_down')")
    if start == -1:
        print("❌ Could not find api_team_drill_down function")
        return content
    
    # Find the date calculations in the function
    date_calc_pattern = r"(\s+# Calculate days ago\n\s+)days_ago = \(datetime\.now\(\) - incident\['Created'\]\)\.days"
    
    # Replace with timezone-aware version
    replacement = r"\1days_ago = (datetime.now(incident['Created'].tzinfo) - incident['Created']).days"
    
    # Apply the replacement
    updated_content = re.sub(date_calc_pattern, replacement, content)
    
    if updated_content == content:
        print("⚠️ No changes made to api_team_drill_down function")
    else:
        print("✅ Fixed timezone issues in api_team_drill_down function")
    
    return updated_content

def fix_all_datetime_calculations(content):
    """Fix all datetime calculations in the code"""
    # Find all datetime.now() - datetime calculations
    pattern = r"datetime\.now\(\) - ([a-zA-Z0-9_\[\]\'\"]+)"
    
    # Replace with timezone-aware version
    replacement = r"datetime.now(\1.tzinfo) - \1"
    
    # Apply the replacement
    updated_content = re.sub(pattern, replacement, content)
    
    if updated_content == content:
        print("⚠️ No changes made to datetime calculations")
    else:
        print(f"✅ Fixed timezone issues in datetime calculations")
    
    return updated_content

def add_timezone_helper_function(content):
    """Add a helper function to ensure consistent timezone handling"""
    # Find a good insertion point - after the parse_month_parameter function
    insertion_point = content.find("# Global variables to store data")
    
    if insertion_point == -1:
        print("❌ Could not find insertion point for timezone helper function")
        return content
    
    # Define the helper function
    helper_function = """
def ensure_timezone_aware(dt, default_tz='UTC'):
    '''Ensure a datetime object has timezone information'''
    if dt is None:
        return None
    
    if isinstance(dt, pd.Timestamp):
        if dt.tzinfo is None:
            return dt.tz_localize(default_tz)
        return dt
    
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            import pytz
            return pytz.timezone(default_tz).localize(dt)
        return dt
    
    return dt

"""
    
    # Insert the helper function at the insertion point
    updated_content = content[:insertion_point] + helper_function + content[insertion_point:]
    
    print("✅ Added timezone helper function")
    
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
    print("🔧 Fixing timezone issues...")
    content = add_timezone_helper_function(content)
    content = fix_api_sla_breach_incidents(content)
    content = fix_api_team_drill_down(content)
    content = fix_all_datetime_calculations(content)
    
    # Write the updated content
    with open(app_py_path, 'w') as f:
        f.write(content)
    
    print("✅ Successfully fixed timezone issues!")
    print("🚀 Restart the dashboard to apply the changes.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
