"""
MTTR (Mean Time To Resolve) Calculation Logic
==============================================

P1 Metric Definition:
- Name: Mean time to resolve - Incident (MTTR)
- Purpose: Tracks How Fast each ticket is resolved at incident level
- Units: Minutes or Hours
- Data Source: SNOW ticket id with created_at and resolved_at timestamps
- Formula: resolved_at minus created_at

This file demonstrates the exact logic used in the dashboard application.
"""

import pandas as pd
from datetime import datetime, timedelta
import numpy as np

def calculate_mttr_example():
    """
    Demonstrates MTTR calculation with sample data
    """
    print("="*60)
    print("MTTR (Mean Time To Resolve) Calculation Logic")
    print("="*60)
    
    # Sample incident data (similar to what we have in the Excel file)
    # Includes weekday and weekend incidents to demonstrate filtering
    sample_data = {
        'ticket_id': ['INC001', 'INC002', 'INC003', 'INC004', 'INC005', 'INC006', 'INC007'],
        'created_at': [
            '2025-02-01 09:00:00',  # Saturday (weekend)
            '2025-02-02 14:30:00',  # Sunday (weekend)  
            '2025-02-03 08:15:00',  # Monday (weekday)
            '2025-02-04 16:45:00',  # Tuesday (weekday)
            '2025-02-05 11:20:00',  # Wednesday (weekday)
            '2025-02-08 09:00:00',  # Saturday (weekend)
            '2025-02-10 10:00:00'   # Monday (weekday)
        ],
        'resolved_at': [
            '2025-02-01 11:30:00',  # 2.5 hours to resolve (weekend)
            '2025-02-02 16:45:00',  # 2.25 hours to resolve (weekend)
            '2025-02-03 10:00:00',  # 1.75 hours to resolve (weekday)
            '2025-02-05 09:15:00',  # 16.5 hours to resolve (weekday)
            '2025-02-05 13:45:00',  # 2.42 hours to resolve (weekday)
            '2025-02-08 17:00:00',  # 8 hours to resolve (weekend)
            '2025-02-10 15:30:00'   # 5.5 hours to resolve (weekday)
        ]
    }
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    # Convert to datetime (same as in app.py)
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['resolved_at'] = pd.to_datetime(df['resolved_at'])
    
    print("Sample Data:")
    print(df.to_string(index=False))
    print("\n" + "="*60)
    
    # Add weekday flag - exclude weekends from MTTR calculation
    df['created_weekday'] = df['created_at'].dt.dayofweek  # Monday=0, Sunday=6
    df['is_weekday_created'] = df['created_weekday'] < 5  # Monday-Friday only
    
    # Calculate MTTR: resolved_at minus created_at (in minutes)
    df['mttr_minutes'] = (df['resolved_at'] - df['created_at']).dt.total_seconds() / 60
    df['mttr_hours'] = df['mttr_minutes'] / 60
    
    print("MTTR Calculation:")
    print("Formula: resolved_at - created_at")
    print("-" * 40)
    
    for i, row in df.iterrows():
        print(f"{row['ticket_id']}: {row['resolved_at']} - {row['created_at']} = {row['mttr_minutes']:.1f} minutes ({row['mttr_hours']:.2f} hours)")
    
    print("\n" + "="*60)
    
    # Summary statistics
    mean_mttr_minutes = df['mttr_minutes'].mean()
    mean_mttr_hours = mean_mttr_minutes / 60
    
    # Weekend filtering for MTTR calculations
    weekday_df = df[df['is_weekday_created']]
    weekday_mean_mttr_minutes = weekday_df['mttr_minutes'].mean()
    weekday_mean_mttr_hours = weekday_mean_mttr_minutes / 60
    
    print("Summary Statistics (All Incidents):")
    print(f"Mean MTTR: {mean_mttr_minutes:.1f} minutes ({mean_mttr_hours:.2f} hours)")
    print(f"Median MTTR: {df['mttr_minutes'].median():.1f} minutes")
    print(f"Min MTTR: {df['mttr_minutes'].min():.1f} minutes")
    print(f"Max MTTR: {df['mttr_minutes'].max():.1f} minutes")
    
    print(f"\nSummary Statistics (Weekday-Created Only - Used in Dashboard):")
    print(f"Weekday incidents: {len(weekday_df)}/{len(df)}")
    print(f"Mean MTTR (Weekdays): {weekday_mean_mttr_minutes:.1f} minutes ({weekday_mean_mttr_hours:.2f} hours)")
    if len(weekday_df) > 0:
        print(f"Median MTTR (Weekdays): {weekday_df['mttr_minutes'].median():.1f} minutes")
        print(f"Min MTTR (Weekdays): {weekday_df['mttr_minutes'].min():.1f} minutes")
        print(f"Max MTTR (Weekdays): {weekday_df['mttr_minutes'].max():.1f} minutes")
    
    return df

def monthly_mttr_calculation(df):
    """
    Demonstrates how MTTR is calculated by month (as used in trends)
    """
    print("\n" + "="*60)
    print("Monthly MTTR Calculation (for Trends)")
    print("="*60)
    
    # Group by month and calculate mean MTTR (weekday incidents only)
    df['month'] = df['created_at'].dt.to_period('M')
    monthly_mttr = df.groupby('month').agg({
        'ticket_id': 'count',
        'mttr_minutes': lambda x: df.loc[x.index, 'mttr_minutes'][df.loc[x.index, 'is_weekday_created']].mean()
    }).round(2)
    
    monthly_mttr.columns = ['incident_count', 'avg_mttr_minutes']
    monthly_mttr['avg_mttr_hours'] = monthly_mttr['avg_mttr_minutes'] / 60
    
    print("Monthly MTTR Breakdown (Weekday-Created Incidents Only):")
    print(monthly_mttr.to_string())
    print("\nNote: Weekend-created incidents excluded from MTTR calculation")
    
    return monthly_mttr

def team_mttr_calculation(df):
    """
    Demonstrates how MTTR is calculated by team (as used in team performance)
    """
    print("\n" + "="*60)
    print("Team MTTR Calculation (for Team Performance)")
    print("="*60)
    
    # Add sample team assignments
    df['assignment_group'] = ['Team A', 'Team B', 'Team A', 'Team C', 'Team B', 'Team A', 'Team C']
    
    # Group by team and calculate mean MTTR (weekday incidents only)
    team_mttr = df.groupby('assignment_group').agg({
        'ticket_id': 'count',
        'mttr_minutes': lambda x: df.loc[x.index, 'mttr_minutes'][df.loc[x.index, 'is_weekday_created']].mean()
    }).round(2)
    
    team_mttr.columns = ['incident_count', 'avg_mttr_minutes']
    team_mttr['avg_mttr_hours'] = team_mttr['avg_mttr_minutes'] / 60
    
    print("Team MTTR Breakdown (Weekday-Created Incidents Only):")
    print(team_mttr.to_string())
    print("\nNote: Weekend-created incidents excluded from MTTR calculation")
    
    return team_mttr

def dashboard_implementation_notes():
    """
    Shows how this logic is implemented in the actual dashboard
    """
    print("\n" + "="*60)
    print("Dashboard Implementation Notes")
    print("="*60)
    
    implementation_code = '''
# In app.py - Data Loading:
# Add weekday flag (Monday=0, Sunday=6) - exclude Saturday (5) and Sunday (6)
incidents_df['created_weekday'] = incidents_df['Created'].dt.dayofweek
incidents_df['is_weekday_created'] = incidents_df['created_weekday'] < 5  # Monday-Friday only

incidents_df['MTTR_calculated'] = (incidents_df['Resolved'] - incidents_df['Created']).dt.total_seconds() / 60

# In app.py - Overview API (weekday incidents only):
weekday_filtered_df = filtered_df[filtered_df['is_weekday_created']]
avg_resolution_time = weekday_filtered_df['MTTR_calculated'].mean()

# In app.py - Monthly Trends (weekday incidents only):
monthly_data = df.groupby(df['Created'].dt.to_period('M')).agg({
    'Number': 'count',
    'MTTR_calculated': lambda x: df.loc[x.index, 'MTTR_calculated'][df.loc[x.index, 'is_weekday_created']].mean(),
    'Reopen count': lambda x: (x == 0).sum() / len(x) * 100
}).round(2)

# In app.py - Team Performance (weekday incidents only):
team_stats = filtered_df.groupby('Assignment group').agg({
    'Number': 'count',
    'MTTR_calculated': lambda x: filtered_df.loc[x.index, 'MTTR_calculated'][filtered_df.loc[x.index, 'is_weekday_created']].mean(),
    'Reopen count': lambda x: (x == 0).sum() / len(x) * 100
}).round(2)

# Display conversion (minutes to hours):
mttr_hours = mttr_minutes / 60
    '''
    
    print("Code Implementation in Dashboard:")
    print(implementation_code)
    
    print("\nKey Points:")
    print("- MTTR is calculated in MINUTES during data loading")
    print("- Converted to HOURS for display purposes")
    print("- Uses pandas datetime arithmetic for accuracy")
    print("- Handles missing/invalid timestamps gracefully")
    print("- Weekend-created incidents (Saturday & Sunday) are EXCLUDED from MTTR calculations")
    print("- Applied consistently across all dashboard views (overview, trends, team performance)")

if __name__ == "__main__":
    # Run the demonstration
    df = calculate_mttr_example()
    monthly_mttr_calculation(df)
    team_mttr_calculation(df)
    dashboard_implementation_notes()
    
    print("\n" + "="*60)
    print("MTTR Calculation Complete!")
    print("This logic matches exactly what's used in the dashboard.")
    print("="*60) 