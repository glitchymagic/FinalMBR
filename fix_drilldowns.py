#!/usr/bin/env python3
"""
Fix for drill-down endpoints in the MBR Dashboard
This script patches the app.py file to fix all drill-down endpoints
"""

import re
import os
import sys
import shutil
from datetime import datetime

def backup_file(file_path):
    """Create a backup of the original file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Created backup: {backup_path}")
    return backup_path

def fix_mttr_drilldown(content):
    """Fix the MTTR drill-down endpoint"""
    pattern = r"""(\s+# Filter by specific month\n\s+)month_start = pd\.to_datetime\(month \+ '-01'\)\n\s+month_end = month_start \+ pd\.DateOffset\(months=1\) - pd\.DateOffset\(days=1\)\n\s+\n\s+month_df = filtered_df\[\n\s+\(filtered_df\['Created'\] >= month_start\) & \n\s+\(filtered_df\['Created'\] <= month_end\)\n\s+\]"""
    
    replacement = r"""\1# Use robust date parsing
    month_start, month_end = parse_month_parameter(month)
    
    if month_start is None or month_end is None:
        return jsonify({'error': f'Could not parse month format: {month}'}), 400
    
    month_df = filtered_df[
        (filtered_df['Created'] >= month_start) & 
        (filtered_df['Created'] <= month_end)
    ]"""
    
    return re.sub(pattern, replacement, content)

def fix_incident_drilldown(content):
    """Fix the incident drill-down endpoint"""
    pattern = r"""(\s+# Filter by specific month\n\s+)month_start = pd\.to_datetime\(month \+ '-01'\)\n\s+month_end = month_start \+ pd\.DateOffset\(months=1\) - pd\.DateOffset\(days=1\)\n\s+\n\s+month_df = filtered_df\[\n\s+\(filtered_df\['Created'\] >= month_start\) & \n\s+\(filtered_df\['Created'\] <= month_end\)\n\s+\]"""
    
    replacement = r"""\1# Use robust date parsing
    month_start, month_end = parse_month_parameter(month)
    
    if month_start is None or month_end is None:
        return jsonify({'error': f'Could not parse month format: {month}'}), 400
    
    month_df = filtered_df[
        (filtered_df['Created'] >= month_start) & 
        (filtered_df['Created'] <= month_end)
    ]"""
    
    return re.sub(pattern, replacement, content)

def fix_fcr_drilldown(content):
    """Fix the FCR drill-down endpoint"""
    pattern = r"""(\s+# Filter by specific month\n\s+)month_start = pd\.to_datetime\(month \+ '-01'\)\n\s+month_end = month_start \+ pd\.DateOffset\(months=1\) - pd\.DateOffset\(days=1\)\n\s+\n\s+month_df = filtered_df\[\n\s+\(filtered_df\['Created'\] >= month_start\) & \n\s+\(filtered_df\['Created'\] <= month_end\)\n\s+\]"""
    
    replacement = r"""\1# Use robust date parsing
    month_start, month_end = parse_month_parameter(month)
    
    if month_start is None or month_end is None:
        return jsonify({'error': f'Could not parse month format: {month}'}), 400
    
    month_df = filtered_df[
        (filtered_df['Created'] >= month_start) & 
        (filtered_df['Created'] <= month_end)
    ]"""
    
    return re.sub(pattern, replacement, content)

def fix_consultations_month_drilldown(content):
    """Fix the consultations month drill-down endpoint"""
    pattern = r"""(\s+# Parse target month\n\s+)try:\n\s+month_parts = target_month\.split\('-'\)\n\s+if len\(month_parts\) == 2:\n\s+year = int\(month_parts\[0\]\)\n\s+month = int\(month_parts\[1\]\)\n\s+\n\s+# Create date range\n\s+month_start = pd\.Timestamp\(f"{year}-{month:02d}-01"\)\n\s+if month == 12:\n\s+month_end = pd\.Timestamp\(f"{year\+1}-01-01"\) - pd\.Timedelta\(days=1\)\n\s+else:\n\s+month_end = pd\.Timestamp\(f"{year}-{month\+1:02d}-01"\) - pd\.Timedelta\(days=1\)"""
    
    replacement = r"""\1# Use robust date parsing
        month_start, month_end = parse_month_parameter(target_month)
        
        if month_start is None or month_end is None:
            return jsonify({'error': f'Could not parse month format: {target_month}'}), 400"""
    
    return re.sub(pattern, replacement, content)

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
    print("🔧 Applying fixes to drill-down endpoints...")
    content = fix_mttr_drilldown(content)
    content = fix_incident_drilldown(content)
    content = fix_fcr_drilldown(content)
    content = fix_consultations_month_drilldown(content)
    
    # Write the updated content
    with open(app_py_path, 'w') as f:
        f.write(content)
    
    print("✅ Successfully fixed drill-down endpoints!")
    print("🚀 Restart the dashboard to apply the changes.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
