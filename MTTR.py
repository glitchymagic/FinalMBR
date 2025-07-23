"""
MTTR (Mean Time To Resolve) Calculation Logic
==============================================

Updated for: Combined_Incidents_Report_Feb_to_June_2025.xlsx
Now uses business hours calculation (excludes weekends)

P1 Metric Definition:
- Name: Mean time to resolve - Incident (MTTR)
- Purpose: Tracks How Fast each ticket is resolved at incident level
- Units: Minutes or Hours
- Data Source: Combined_Incidents_Report_Feb_to_June_2025.xlsx with Created/Resolved timestamps and Resolve time
- Formula: Business hours between resolved_at and created_at (excluding weekends)

This file demonstrates the exact logic used in the dashboard application.
"""

import pandas as pd
from datetime import datetime, timedelta
import numpy as np

def calculate_business_minutes(start_date, end_date):
    """
    Calculate minutes between two dates excluding weekends
    This is the core business hours calculation logic
    """
    if pd.isna(start_date) or pd.isna(end_date):
        return np.nan
    
    # Ensure we're working with datetime objects
    if isinstance(start_date, str):
        start_date = pd.to_datetime(start_date)
    if isinstance(end_date, str):
        end_date = pd.to_datetime(end_date)
    
    # If end date is before start date, return 0
    if end_date < start_date:
        return 0
    
    total_minutes = 0
    current = start_date
    
    while current < end_date:
        # If it's a weekday (Monday=0 to Friday=4)
        if current.weekday() < 5:
            # Calculate minutes until end of day or end_date
            next_day = current.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + timedelta(days=1)
            segment_end = min(end_date, next_day)
            
            # Add minutes for this segment
            segment_minutes = (segment_end - current).total_seconds() / 60
            total_minutes += segment_minutes
        
        # Move to next day
        current = current.replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)
    
    return total_minutes

def load_new_incident_data():
    """
    Load the new Combined_Incidents_Report_Feb_to_June_2025.xlsx data
    """
    print("Loading new incident data from Combined_Incidents_Report_Feb_to_June_2025.xlsx...")
    try:
        df = pd.read_excel('Combined_Incidents_Report_Feb_to_June_2025.xlsx')
        
        # Convert date columns
        df['Created'] = pd.to_datetime(df['Created'])
        df['Resolved'] = pd.to_datetime(df['Resolved'])
        
        # Convert resolve time to numeric
        df['Resolve time'] = pd.to_numeric(df['Resolve time'], errors='coerce')
        
        # Add weekday flag (Monday=0, Sunday=6) - for reporting purposes
        df['created_weekday'] = df['Created'].dt.dayofweek
        df['is_weekday_created'] = df['created_weekday'] < 5  # Monday-Friday only
        
        # Calculate MTTR using business hours (excluding weekends)
        df['MTTR_business_minutes'] = df.apply(
            lambda row: calculate_business_minutes(row['Created'], row['Resolved']),
            axis=1
        )
        
        # For backwards compatibility, also keep the total elapsed time
        df['MTTR_total_minutes'] = df.apply(
            lambda row: (row['Resolved'] - row['Created']).total_seconds() / 60 
            if pd.notna(row['Resolved']) and pd.notna(row['Created']) else np.nan,
            axis=1
        )
        
        print(f"✅ Data loaded successfully: {len(df)} incidents")
        print(f"📅 Date range: {df['Created'].min()} to {df['Created'].max()}")
        print(f"⏱️  Resolve time range: {df['Resolve time'].min():.1f} to {df['Resolve time'].max():.1f} minutes")
        print(f"👥 Assignment groups: {df['Assignment group'].nunique()}")
        print(f"📊 Weekday created: {df['is_weekday_created'].sum()}, Weekend created: {(~df['is_weekday_created']).sum()}")
        
        return df
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None 

def calculate_mttr_example():
    """
    Demonstrates MTTR calculation with sample data using business hours
    """
    print("="*60)
    print("MTTR (Mean Time To Resolve) Calculation Logic")
    print("Business Hours Calculation (Excluding Weekends)")
    print("="*60)
    
    # Sample incident data to demonstrate business hours calculation
    sample_data = {
        'ticket_id': ['INC001', 'INC002', 'INC003', 'INC004', 'INC005'],
        'created_at': [
            '2025-02-07 09:00:00',  # Friday morning
            '2025-02-07 16:00:00',  # Friday afternoon  
            '2025-02-03 08:15:00',  # Monday morning
            '2025-02-04 16:45:00',  # Tuesday afternoon
            '2025-02-05 11:20:00',  # Wednesday morning
        ],
        'resolved_at': [
            '2025-02-10 10:00:00',  # Monday morning (spans weekend)
            '2025-02-10 09:00:00',  # Monday morning (spans weekend)
            '2025-02-03 10:00:00',  # Monday morning (same day)
            '2025-02-05 09:15:00',  # Wednesday morning (next day)
            '2025-02-05 13:45:00',  # Wednesday afternoon (same day)
        ]
    }
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    # Convert to datetime
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['resolved_at'] = pd.to_datetime(df['resolved_at'])
    
    print("Sample Data:")
    print(df.to_string(index=False))
    print("\n" + "="*60)
    
    # Calculate both total time and business hours MTTR
    df['total_elapsed_minutes'] = (df['resolved_at'] - df['created_at']).dt.total_seconds() / 60
    df['mttr_business_minutes'] = df.apply(
        lambda row: calculate_business_minutes(row['created_at'], row['resolved_at']),
        axis=1
    )
    df['mttr_business_hours'] = df['mttr_business_minutes'] / 60
    
    print("MTTR Calculation Comparison:")
    print("Total Elapsed Time vs Business Hours Only")
    print("-" * 60)
    
    for i, row in df.iterrows():
        print(f"\n{row['ticket_id']}:")
        print(f"  Created: {row['created_at']}")
        print(f"  Resolved: {row['resolved_at']}")
        print(f"  Total elapsed: {row['total_elapsed_minutes']:.1f} min ({row['total_elapsed_minutes']/60:.1f} hrs)")
        print(f"  Business hours: {row['mttr_business_minutes']:.1f} min ({row['mttr_business_hours']:.1f} hrs)")
        print(f"  Weekend time excluded: {row['total_elapsed_minutes'] - row['mttr_business_minutes']:.1f} min")
    
    print("\n" + "="*60)
    
    # Summary statistics
    mean_total_minutes = df['total_elapsed_minutes'].mean()
    mean_business_minutes = df['mttr_business_minutes'].mean()
    
    print("Summary Statistics:")
    print(f"Mean MTTR (Total elapsed): {mean_total_minutes:.1f} minutes ({mean_total_minutes/60:.1f} hours)")
    print(f"Mean MTTR (Business hours): {mean_business_minutes:.1f} minutes ({mean_business_minutes/60:.1f} hours)")
    print(f"Average weekend time excluded: {mean_total_minutes - mean_business_minutes:.1f} minutes")
    
    return df

def monthly_mttr_calculation(df):
    """
    Demonstrates how MTTR is calculated by month using business hours
    """
    print("\n" + "="*60)
    print("Monthly MTTR Calculation (Business Hours)")
    print("="*60)
    
    # Group by month and calculate mean MTTR
    df['month'] = df['created_at'].dt.to_period('M')
    monthly_mttr = df.groupby('month').agg({
        'ticket_id': 'count',
        'mttr_business_minutes': 'mean',
        'total_elapsed_minutes': 'mean'
    }).round(2)
    
    monthly_mttr.columns = ['incident_count', 'avg_mttr_business_minutes', 'avg_total_minutes']
    monthly_mttr['avg_mttr_business_hours'] = monthly_mttr['avg_mttr_business_minutes'] / 60
    monthly_mttr['weekend_time_saved'] = monthly_mttr['avg_total_minutes'] - monthly_mttr['avg_mttr_business_minutes']
    
    print("Monthly MTTR Breakdown:")
    print(monthly_mttr.to_string())
    print("\nNote: Business hours calculation excludes all weekend time")
    
    return monthly_mttr

def team_mttr_calculation(df):
    """
    Demonstrates how MTTR is calculated by team using business hours
    """
    print("\n" + "="*60)
    print("Team MTTR Calculation (Business Hours)")
    print("="*60)
    
    # Add sample team assignments
    df['assignment_group'] = ['Team A', 'Team B', 'Team A', 'Team C', 'Team B']
    
    # Group by team and calculate mean MTTR
    team_mttr = df.groupby('assignment_group').agg({
        'ticket_id': 'count',
        'mttr_business_minutes': 'mean',
        'total_elapsed_minutes': 'mean'
    }).round(2)
    
    team_mttr.columns = ['incident_count', 'avg_mttr_business_minutes', 'avg_total_minutes']
    team_mttr['avg_mttr_business_hours'] = team_mttr['avg_mttr_business_minutes'] / 60
    
    print("Team MTTR Breakdown:")
    print(team_mttr.to_string())
    print("\nNote: Using business hours calculation for accurate SLA tracking")
    
    return team_mttr 

def sla_compliance_calculation(df):
    """
    Demonstrates SLA compliance calculation using business hours MTTR
    """
    print("\n" + "="*60)
    print("SLA Compliance Calculation (Business Hours)")
    print("="*60)
    
    # Define SLA thresholds
    SLA_BASELINE_MINUTES = 240  # 4 hours
    SLA_GOAL_MINUTES = 180      # 3 hours
    
    # Calculate SLA compliance using business hours MTTR
    df['sla_met_baseline'] = df['mttr_business_minutes'] <= SLA_BASELINE_MINUTES
    df['sla_met_goal'] = df['mttr_business_minutes'] <= SLA_GOAL_MINUTES
    df['sla_breached'] = df['mttr_business_minutes'] > SLA_BASELINE_MINUTES
    df['sla_variance_minutes'] = df['mttr_business_minutes'] - SLA_BASELINE_MINUTES
    
    print(f"SLA Thresholds:")
    print(f"  Baseline: {SLA_BASELINE_MINUTES} minutes ({SLA_BASELINE_MINUTES/60:.1f} hours)")
    print(f"  Goal: {SLA_GOAL_MINUTES} minutes ({SLA_GOAL_MINUTES/60:.1f} hours)")
    print("\nSLA Compliance Results:")
    
    for i, row in df.iterrows():
        print(f"\n{row['ticket_id']}:")
        print(f"  Business Hours MTTR: {row['mttr_business_minutes']:.1f} min")
        print(f"  Baseline SLA Met: {'✅ Yes' if row['sla_met_baseline'] else '❌ No'}")
        print(f"  Goal SLA Met: {'✅ Yes' if row['sla_met_goal'] else '❌ No'}")
        if row['sla_breached']:
            print(f"  SLA Variance: {row['sla_variance_minutes']:.1f} min over baseline")
    
    # Summary statistics
    baseline_compliance = (df['sla_met_baseline'].sum() / len(df)) * 100
    goal_compliance = (df['sla_met_goal'].sum() / len(df)) * 100
    breach_rate = (df['sla_breached'].sum() / len(df)) * 100
    
    print("\n" + "-" * 40)
    print("Overall SLA Compliance:")
    print(f"  Baseline (240 min): {baseline_compliance:.1f}%")
    print(f"  Goal (180 min): {goal_compliance:.1f}%")
    print(f"  Breach Rate: {breach_rate:.1f}%")
    
    return df

def dashboard_implementation_notes():
    """
    Shows how to implement business hours MTTR in the dashboard
    """
    print("\n" + "="*60)
    print("Dashboard Implementation Notes - Business Hours MTTR")
    print("="*60)
    
    implementation_code = '''
# UPDATED app.py - Data Loading Section:
# Import the business hours calculation function
from MTTR import calculate_business_minutes

# In load_data() function:
# Calculate MTTR using business hours instead of total elapsed time
incidents_df['MTTR_business_minutes'] = incidents_df.apply(
    lambda row: calculate_business_minutes(row['Created'], row['Resolved']),
    axis=1
)

# Keep the original calculation for comparison/backwards compatibility
incidents_df['MTTR_total_minutes'] = (
    incidents_df['Resolved'] - incidents_df['Created']
).dt.total_seconds() / 60

# Update SLA calculations to use business hours MTTR
incidents_df['sla_met_mttr'] = incidents_df['MTTR_business_minutes'] <= SLA_THRESHOLD_MINUTES
incidents_df['sla_met_goal'] = incidents_df['MTTR_business_minutes'] <= SLA_GOAL_MINUTES
incidents_df['sla_breached'] = incidents_df['MTTR_business_minutes'] > incidents_df['sla_promised_minutes']
incidents_df['sla_variance_minutes'] = incidents_df['MTTR_business_minutes'] - incidents_df['sla_promised_minutes']

# In api_overview() and other endpoints:
# Use MTTR_business_minutes instead of MTTR_calculated
avg_resolution_time = filtered_df['MTTR_business_minutes'].mean()

# For monthly/team aggregations:
'MTTR_business_minutes': 'mean'  # Instead of the lambda with weekday filter

# Display conversion (minutes to hours):
mttr_hours = mttr_business_minutes / 60
    '''
    
    print("Key Changes for Dashboard:")
    print(implementation_code)
    
    print("\nKey Implementation Points:")
    print("1. Import calculate_business_minutes() function from MTTR.py")
    print("2. Replace MTTR_calculated with MTTR_business_minutes throughout")
    print("3. Remove weekday filtering - business hours calc handles this properly")
    print("4. All SLA calculations now use accurate business hours")
    print("5. Weekend time is automatically excluded from all calculations")
    print("\nBenefits:")
    print("- More accurate SLA tracking")
    print("- Fair measurement excluding non-business hours")
    print("- Aligns with industry standard practices")
    print("- No penalty for incidents spanning weekends")

def analyze_real_data():
    """
    Analyze MTTR using the actual data with business hours calculation
    """
    df = load_new_incident_data()
    if df is None:
        print("❌ Cannot proceed without data")
        return
    
    print("\n" + "="*60)
    print("🔍 REAL DATA MTTR ANALYSIS (Business Hours)")
    print("="*60)
    
    # Compare total elapsed vs business hours MTTR
    resolved_df = df[df['Resolved'].notna()]
    
    overall_mean_total = resolved_df['MTTR_total_minutes'].mean()
    overall_mean_business = resolved_df['MTTR_business_minutes'].mean()
    
    print(f"📊 MTTR COMPARISON:")
    print(f"   Total Incidents: {len(df):,}")
    print(f"   Resolved Incidents: {len(resolved_df):,}")
    print()
    print(f"   Average MTTR (Total elapsed): {overall_mean_total:.1f} min ({overall_mean_total/60:.1f} hrs)")
    print(f"   Average MTTR (Business hours): {overall_mean_business:.1f} min ({overall_mean_business/60:.1f} hrs)")
    print(f"   Average weekend time excluded: {overall_mean_total - overall_mean_business:.1f} min")
    print(f"   Time reduction: {((overall_mean_total - overall_mean_business) / overall_mean_total * 100):.1f}%")
    
    # SLA compliance comparison
    SLA_BASELINE = 240  # 4 hours
    SLA_GOAL = 180      # 3 hours
    
    # Using total elapsed time
    sla_met_total = (resolved_df['MTTR_total_minutes'] <= SLA_BASELINE).sum()
    sla_goal_total = (resolved_df['MTTR_total_minutes'] <= SLA_GOAL).sum()
    
    # Using business hours
    sla_met_business = (resolved_df['MTTR_business_minutes'] <= SLA_BASELINE).sum()
    sla_goal_business = (resolved_df['MTTR_business_minutes'] <= SLA_GOAL).sum()
    
    print(f"\n📈 SLA COMPLIANCE IMPACT:")
    print(f"   Baseline SLA (240 min):")
    print(f"     Total elapsed: {sla_met_total:,}/{len(resolved_df):,} ({sla_met_total/len(resolved_df)*100:.1f}%)")
    print(f"     Business hours: {sla_met_business:,}/{len(resolved_df):,} ({sla_met_business/len(resolved_df)*100:.1f}%)")
    print(f"     Improvement: +{sla_met_business - sla_met_total:,} incidents ({(sla_met_business - sla_met_total)/len(resolved_df)*100:.1f}%)")
    print()
    print(f"   Goal SLA (180 min):")
    print(f"     Total elapsed: {sla_goal_total:,}/{len(resolved_df):,} ({sla_goal_total/len(resolved_df)*100:.1f}%)")
    print(f"     Business hours: {sla_goal_business:,}/{len(resolved_df):,} ({sla_goal_business/len(resolved_df)*100:.1f}%)")
    print(f"     Improvement: +{sla_goal_business - sla_goal_total:,} incidents ({(sla_goal_business - sla_goal_total)/len(resolved_df)*100:.1f}%)")
    
    # Monthly breakdown with business hours
    print(f"\n📅 MONTHLY MTTR BREAKDOWN (Business Hours):")
    df['created_month'] = df['Created'].dt.to_period('M')
    monthly_mttr = df.groupby('created_month').agg({
        'Number': 'count',
        'MTTR_business_minutes': 'mean',
        'MTTR_total_minutes': 'mean'
    }).round(1)
    monthly_mttr.columns = ['incidents', 'avg_business_minutes', 'avg_total_minutes']
    monthly_mttr['avg_business_hours'] = monthly_mttr['avg_business_minutes'] / 60
    monthly_mttr['weekend_excluded'] = monthly_mttr['avg_total_minutes'] - monthly_mttr['avg_business_minutes']
    
    for month, row in monthly_mttr.iterrows():
        print(f"   {month}: {row['incidents']:,} incidents, Business MTTR: {row['avg_business_minutes']:.1f} min ({row['avg_business_hours']:.1f} hrs)")
    
    return df

if __name__ == "__main__":
    print("⏱️  MTTR (Mean Time To Resolve) Analysis - Business Hours")
    print("📁 Using: Combined_Incidents_Report_Feb_to_June_2025.xlsx")
    
    # Run real data analysis first
    real_df = analyze_real_data()
    
    # Then run the demonstration with sample data
    print("\n" + "="*60)
    print("📚 DEMONSTRATION WITH SAMPLE DATA")
    print("="*60)
    df = calculate_mttr_example()
    monthly_mttr_calculation(df)
    team_mttr_calculation(df)
    sla_compliance_calculation(df)
    dashboard_implementation_notes()
    
    print("\n" + "="*60)
    print("✅ MTTR Analysis Complete!")
    print("Business hours calculation provides more accurate SLA tracking.")
    print("="*60) 