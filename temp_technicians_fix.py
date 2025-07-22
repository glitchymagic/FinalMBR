    # Handle missing technician names by marking as 'Unassigned'
    total_before_filter = len(filtered_incidents)
    missing_resolved_by = filtered_incidents['Resolved by'].isna() | (filtered_incidents['Resolved by'] == '')
    missing_count = missing_resolved_by.sum()
    
    # Fill missing technician names with 'Unassigned' to maintain total consistency
    filtered_incidents['Resolved by'] = filtered_incidents['Resolved by'].fillna('Unassigned')
    filtered_incidents.loc[filtered_incidents['Resolved by'] == '', 'Resolved by'] = 'Unassigned'
    
    print(f"🔍 TECHNICIANS API: {total_before_filter} total incidents, {missing_count} marked as 'Unassigned'")
    print(f"📊 TECHNICIANS API: {len(filtered_incidents)} incidents (100% consistency with dashboard)")
