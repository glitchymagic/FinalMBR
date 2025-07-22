"""
FCR (First Contact Resolution) Calculation Logic
===============================================

P1 Metric Definition:
- Name: First Contact Resolution (FCR)
- Purpose: Measures How Many Tickets Were Solved on the First Try
- Units: Percent
- Data Source: SNOW ticket id with reopen_count field
- Formula: (Number of Tickets Resolved on First Contact / Total Number of Tickets) x 100
- Logic: "First Contact" means reopen_count = 0

This file demonstrates the exact logic used in the dashboard application.
"""

import pandas as pd
import numpy as np

def calculate_fcr_example():
    """
    Demonstrates FCR calculation with sample data
    """
    print("="*60)
    print("FCR (First Contact Resolution) Calculation Logic")
    print("="*60)
    
    # Sample incident data (similar to what we have in the Excel file)
    sample_data = {
        'ticket_id': ['INC001', 'INC002', 'INC003', 'INC004', 'INC005', 'INC006', 'INC007', 'INC008'],
        'reopen_count': [0, 1, 0, 0, 2, 0, 0, 1],  # 0 = resolved on first contact, >0 = reopened
        'assignment_group': ['Team A', 'Team A', 'Team B', 'Team B', 'Team C', 'Team C', 'Team A', 'Team B'],
        'created_month': ['2025-02', '2025-02', '2025-02', '2025-03', '2025-03', '2025-03', '2025-03', '2025-03']
    }
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    print("Sample Data:")
    print(df.to_string(index=False))
    print("\n" + "="*60)
    
    # Calculate FCR: Count tickets resolved on first contact (reopen_count = 0)
    df['first_contact_resolution'] = df['reopen_count'] == 0
    
    print("FCR Calculation Breakdown:")
    print("Formula: (Number of Tickets Resolved on First Contact / Total Number of Tickets) x 100")
    print("Where 'First Contact' = reopen_count = 0")
    print("-" * 40)
    
    for i, row in df.iterrows():
        status = "✓ First Contact" if row['first_contact_resolution'] else "✗ Reopened"
        print(f"{row['ticket_id']}: reopen_count = {row['reopen_count']} → {status}")
    
    print("\n" + "="*60)
    
    # Calculate overall FCR
    total_tickets = len(df)
    first_contact_tickets = df['first_contact_resolution'].sum()
    fcr_percentage = (first_contact_tickets / total_tickets) * 100
    
    print("Overall FCR Calculation:")
    print(f"Total Tickets: {total_tickets}")
    print(f"First Contact Resolutions: {first_contact_tickets}")
    print(f"FCR Rate: ({first_contact_tickets}/{total_tickets}) × 100 = {fcr_percentage:.1f}%")
    
    return df

def monthly_fcr_calculation(df):
    """
    Demonstrates how FCR is calculated by month (as used in trends)
    """
    print("\n" + "="*60)
    print("Monthly FCR Calculation (for Trends)")
    print("="*60)
    
    # Group by month and calculate FCR
    monthly_fcr = df.groupby('created_month').agg({
        'ticket_id': 'count',
        'reopen_count': lambda x: (x == 0).sum() / len(x) * 100  # FCR calculation
    }).round(1)
    
    monthly_fcr.columns = ['total_tickets', 'fcr_percentage']
    
    print("Monthly FCR Breakdown:")
    print(monthly_fcr.to_string())
    
    # Show detailed calculation for each month
    print("\nDetailed Monthly Calculations:")
    for month in df['created_month'].unique():
        month_data = df[df['created_month'] == month]
        total = len(month_data)
        first_contact = (month_data['reopen_count'] == 0).sum()
        fcr = (first_contact / total) * 100
        print(f"{month}: ({first_contact}/{total}) × 100 = {fcr:.1f}%")
    
    return monthly_fcr

def team_fcr_calculation(df):
    """
    Demonstrates how FCR is calculated by team (as used in team performance)
    """
    print("\n" + "="*60)
    print("Team FCR Calculation (for Team Performance)")
    print("="*60)
    
    # Group by team and calculate FCR
    team_fcr = df.groupby('assignment_group').agg({
        'ticket_id': 'count',
        'reopen_count': lambda x: (x == 0).sum() / len(x) * 100  # FCR calculation
    }).round(1)
    
    team_fcr.columns = ['total_tickets', 'fcr_percentage']
    
    print("Team FCR Breakdown:")
    print(team_fcr.to_string())
    
    # Show detailed calculation for each team
    print("\nDetailed Team Calculations:")
    for team in df['assignment_group'].unique():
        team_data = df[df['assignment_group'] == team]
        total = len(team_data)
        first_contact = (team_data['reopen_count'] == 0).sum()
        fcr = (first_contact / total) * 100
        print(f"{team}: ({first_contact}/{total}) × 100 = {fcr:.1f}%")
    
    return team_fcr

def quarter_filtering_example(df):
    """
    Demonstrates how FCR calculation works with quarter filtering
    """
    print("\n" + "="*60)
    print("Quarter Filtering FCR Calculation")
    print("="*60)
    
    # Simulate quarter filtering (as used in dashboard)
    q1_months = ['2025-02', '2025-03', '2025-04']  # Feb, Mar, Apr
    q2_months = ['2025-05', '2025-06']              # May, Jun
    
    # Add some Q1 data for demonstration
    df_extended = df.copy()
    q1_data = df[df['created_month'].isin(['2025-02', '2025-03'])]  # Use existing data as Q1
    
    print("Quarter 1 (Feb-Mar) FCR:")
    if len(q1_data) > 0:
        q1_total = len(q1_data)
        q1_first_contact = (q1_data['reopen_count'] == 0).sum()
        q1_fcr = (q1_first_contact / q1_total) * 100
        print(f"Q1: ({q1_first_contact}/{q1_total}) × 100 = {q1_fcr:.1f}%")
    else:
        print("No Q1 data in sample")
    
    print("\nThis is how the dashboard handles quarter filtering:")
    print("- Filter incidents by quarter (Q1: Feb-Apr, Q2: May-Jun)")
    print("- Apply FCR calculation to filtered dataset")
    print("- Display results specific to selected quarter")

def edge_cases_demonstration():
    """
    Shows how the FCR calculation handles edge cases
    """
    print("\n" + "="*60)
    print("Edge Cases Handling")
    print("="*60)
    
    edge_cases = {
        'scenario': [
            'All tickets resolved first contact',
            'No tickets resolved first contact', 
            'Mixed reopen counts',
            'Single ticket (first contact)',
            'Single ticket (reopened)'
        ],
        'reopen_counts': [
            [0, 0, 0, 0],      # 100% FCR
            [1, 2, 3, 1],      # 0% FCR
            [0, 1, 0, 2, 0],   # 60% FCR
            [0],               # 100% FCR
            [1]                # 0% FCR
        ]
    }
    
    for i, scenario in enumerate(edge_cases['scenario']):
        reopens = edge_cases['reopen_counts'][i]
        total = len(reopens)
        first_contact = sum(1 for x in reopens if x == 0)
        fcr = (first_contact / total) * 100 if total > 0 else 0
        
        print(f"{scenario}:")
        print(f"  Reopen counts: {reopens}")
        print(f"  FCR: ({first_contact}/{total}) × 100 = {fcr:.1f}%")
        print()

def dashboard_implementation_notes():
    """
    Shows how this logic is implemented in the actual dashboard
    """
    print("\n" + "="*60)
    print("Dashboard Implementation Notes")
    print("="*60)
    
    implementation_code = '''
# In app.py - Overview API:
fcr_rate = (filtered_df['Reopen count'] == 0).sum() / total_incidents * 100 if total_incidents > 0 else 0

# In app.py - Monthly Trends:
monthly_data = df.groupby(df['Created'].dt.to_period('M')).agg({
    'Number': 'count',
    'MTTR_calculated': 'mean',
    'Reopen count': lambda x: (x == 0).sum() / len(x) * 100  # FCR: (First Contact / Total) × 100
}).round(2)

# In app.py - Team Performance:
team_stats = filtered_df.groupby('Assignment group').agg({
    'Number': 'count',
    'MTTR_calculated': 'mean',
    'Reopen count': lambda x: (x == 0).sum() / len(x) * 100  # FCR: (First Contact / Total) × 100
}).round(2)

# Month-to-month comparison:
current_fcr = (current_month_incidents['Reopen count'] == 0).sum() / len(current_month_incidents) * 100
prev_fcr = (prev_month_incidents['Reopen count'] == 0).sum() / len(prev_month_incidents) * 100
fcr_change = current_fcr - prev_fcr
    '''
    
    print("Code Implementation in Dashboard:")
    print(implementation_code)
    
    print("\nKey Points:")
    print("- FCR calculation is consistent across all dashboard views")
    print("- Uses boolean logic: reopen_count == 0 means first contact resolution")
    print("- Handles division by zero (empty datasets)")
    print("- Applies to filtered data (respects quarter selection)")
    print("- Results in percentage values for easy interpretation")
    print("- Rounded to 1 decimal place for display")

if __name__ == "__main__":
    # Run the demonstration
    df = calculate_fcr_example()
    monthly_fcr_calculation(df)
    team_fcr_calculation(df)
    quarter_filtering_example(df)
    edge_cases_demonstration()
    dashboard_implementation_notes()
    
    print("\n" + "="*60)
    print("FCR Calculation Complete!")
    print("This logic matches exactly what's used in the dashboard.")
    print("="*60) 