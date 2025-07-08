#!/usr/bin/env python3
"""
Fix missing API endpoints in the MBR Dashboard
"""

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
    
    # Add the missing endpoints
    print("🔧 Adding missing API endpoints...")
    
    # Find a good insertion point - before the API technicians endpoint
    insertion_point = content.find("@app.route('/api/technicians')")
    
    if insertion_point == -1:
        print("❌ Could not find insertion point for new endpoints")
        return 1
    
    # Define the new endpoints
    new_endpoints = """
@app.route('/api/consultations/frequent-visitors')
def api_consultations_frequent_visitors():
    '''Get frequent visitors (customers with most consultations)'''
    if consultations_df is None:
        return jsonify({'error': 'Consultation data not loaded'}), 500
    
    quarter = request.args.get('quarter', 'all')
    month = request.args.get('month', 'all')
    location = request.args.get('location', 'all')
    region = request.args.get('region', 'all')
    
    # Apply filters
    filtered_df = apply_consultation_filters(consultations_df, quarter, location, region, month)
    
    # Count consultations by visitor name
    visitor_counts = filtered_df['Name'].value_counts().head(10)  # Top 10 frequent visitors
    
    frequent_visitors = []
    for name, count in visitor_counts.items():
        if pd.notna(name) and str(name).strip() != '':
            # Get additional info for this visitor
            visitor_data = filtered_df[filtered_df['Name'] == name]
            completion_rate = (visitor_data['Consult Complete'] == 'Yes').sum() / len(visitor_data) * 100
            most_common_issue = visitor_data['Issue'].value_counts().index[0] if len(visitor_data) > 0 else 'N/A'
            
            frequent_visitors.append({
                'name': str(name),
                'consultation_count': int(count),
                'completion_rate': round(completion_rate, 1),
                'most_common_issue': str(most_common_issue)[:50] + '...' if len(str(most_common_issue)) > 50 else str(most_common_issue),
                'last_consultation': visitor_data['Created'].max().strftime('%Y-%m-%d')
            })
    
    return jsonify({
        'frequent_visitors': frequent_visitors,
        'total_unique_visitors': filtered_df['Name'].nunique(),
        'quarter': quarter,
        'month': month,
        'location': location,
        'region': region
    })

@app.route('/api/consultations/equipment-breakdown')
def api_consultations_equipment_breakdown():
    '''Get equipment type breakdown for bar chart'''
    if consultations_df is None:
        return jsonify({'error': 'Consultation data not loaded'}), 500
    
    quarter = request.args.get('quarter', 'all')
    month = request.args.get('month', 'all')
    location = request.args.get('location', 'all')
    region = request.args.get('region', 'all')
    
    # Apply filters
    filtered_df = apply_consultation_filters(consultations_df, quarter, location, region, month)
    
    # Filter for equipment consultations only
    equipment_df = filtered_df[filtered_df['Consultation Defined'] == 'Equipment']
    
    if len(equipment_df) == 0:
        # Return empty data instead of 404 error
        return jsonify({
            'equipment_breakdown': [],
            'total_equipment_consultations': 0,
            'unique_equipment_types': 0,
            'quarter': quarter,
            'month': month,
            'location': location,
            'region': region
        })
    
    # Count by equipment type
    equipment_counts = equipment_df['Equipment Type'].value_counts()
    
    equipment_data = []
    colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']
    
    for i, (equipment_type, count) in enumerate(equipment_counts.items()):
        if pd.notna(equipment_type) and str(equipment_type).strip() != '':
            equipment_data.append({
                'type': str(equipment_type),
                'count': int(count),
                'percentage': round((count / len(equipment_df)) * 100, 1),
                'color': colors[i % len(colors)]
            })
    
    return jsonify({
        'equipment_breakdown': equipment_data,
        'total_equipment_consultations': len(equipment_df),
        'unique_equipment_types': len(equipment_data),
        'quarter': quarter,
        'month': month,
        'location': location,
        'region': region
    })

@app.route('/api/consultations/types-ranking')
def api_consultations_types_ranking():
    '''Get consultation types ranking from most to least requested'''
    if consultations_df is None:
        return jsonify({'error': 'Consultation data not loaded'}), 500
    
    quarter = request.args.get('quarter', 'all')
    month = request.args.get('month', 'all')
    location = request.args.get('location', 'all')
    region = request.args.get('region', 'all')
    
    # Apply filters
    filtered_df = apply_consultation_filters(consultations_df, quarter, location, region, month)
    
    # Count by consultation type
    type_counts = filtered_df['Consultation Defined'].value_counts()
    
    consultation_types = []
    rank_colors = ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']
    
    for i, (consultation_type, count) in enumerate(type_counts.items()):
        if pd.notna(consultation_type) and str(consultation_type).strip() != '':
            completion_rate = ((filtered_df[filtered_df['Consultation Defined'] == consultation_type]['Consult Complete'] == 'Yes').sum() / count) * 100
            
            consultation_types.append({
                'rank': i + 1,
                'type': str(consultation_type),
                'count': int(count),
                'percentage': round((count / len(filtered_df)) * 100, 1),
                'completion_rate': round(completion_rate, 1),
                'color': rank_colors[i % len(rank_colors)]
            })
    
    return jsonify({
        'consultation_types': consultation_types,
        'total_consultations': len(filtered_df),
        'unique_consultation_types': len(consultation_types),
        'quarter': quarter,
        'month': month,
        'location': location,
        'region': region
    })
"""
    
    # Insert the new endpoints at the insertion point
    updated_content = content[:insertion_point] + new_endpoints + content[insertion_point:]
    
    # Fix the month drill-down endpoint to handle missing month parameter
    month_drill_down_start = updated_content.find("@app.route('/api/consultations/month-drilldown')")
    month_drill_down_check = updated_content.find("if not month or month == 'all':", month_drill_down_start)
    
    if month_drill_down_start != -1 and month_drill_down_check != -1:
        # Find the end of the check line
        line_end = updated_content.find("\n", month_drill_down_check)
        
        # Replace the check with a default value
        updated_content = updated_content[:month_drill_down_check] + """if not month or month == 'all':
        # Use current month as default
        current_date = datetime.now()
        month = f"{current_date.year}-{current_date.month:02d}"
        print(f"Month parameter not provided, using current month: {month}")""" + updated_content[line_end:]
    
    # Write the updated content
    with open(app_py_path, 'w') as f:
        f.write(updated_content)
    
    print("✅ Successfully added missing API endpoints!")
    print("✅ Fixed month drill-down to use current month as default")
    print("🚀 Restart the dashboard to apply the changes.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
