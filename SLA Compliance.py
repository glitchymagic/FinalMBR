"""
SLA Compliance Calculation Logic
================================

Updated for: Combined_Incidents_Report_Feb_to_June_2025.xlsx

SLA Metric Definition:
- Name: SLA Compliance Rate
- Purpose: Tracks percentage of incidents meeting the SLA time requirement
- Units: Percentage (%)
- Data Source: Combined_Incidents_Report_Feb_to_June_2025.xlsx with Made SLA field and MTTR calculations
- Multiple SLA Metrics:
  * Native SLA: Uses "Made SLA" field from source system (Primary metric)
  * MTTR-based SLA: MTTR <= 240 minutes (4 hours baseline)
  * Goal SLA: MTTR <= 180 minutes (3 hours goal)

This file demonstrates the exact logic used in the dashboard application.
Now updated to work with the new Excel data source.
"""

import pandas as pd
from datetime import datetime, timedelta
import numpy as np

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
        
        # Add weekday flag (Monday=0, Sunday=6) - exclude Saturday (5) and Sunday (6)
        df['created_weekday'] = df['Created'].dt.dayofweek
        df['is_weekday_created'] = df['created_weekday'] < 5  # Monday-Friday only
        
        # Calculate MTTR from existing Resolve time column (already in minutes)
        df['MTTR_calculated'] = df['Resolve time'].fillna(0)
        
        # For incidents without resolve time but are resolved, calculate from dates
        no_resolve_time_mask = (df['Resolve time'].isna()) & (df['Resolved'].notna())
        df.loc[no_resolve_time_mask, 'MTTR_calculated'] = (
            df.loc[no_resolve_time_mask, 'Resolved'] - 
            df.loc[no_resolve_time_mask, 'Created']
        ).dt.total_seconds() / 60
        
        # Calculate SLA compliance based on MTTR (240 minutes = 4 hours baseline)
        SLA_THRESHOLD_MINUTES = 240  # Baseline SLA: 4 hours (240 minutes)
        SLA_GOAL_MINUTES = 180       # Goal SLA: 3 hours (180 minutes)
        df['sla_met_mttr'] = df['MTTR_calculated'] <= SLA_THRESHOLD_MINUTES
        df['sla_met_goal'] = df['MTTR_calculated'] <= SLA_GOAL_MINUTES
        
        # Use the existing 'Made SLA' column for primary SLA tracking
        df['sla_met_native'] = df['Made SLA'].fillna(False)
        
        print(f"✅ Data loaded successfully: {len(df)} incidents")
        print(f"📅 Date range: {df['Created'].min()} to {df['Created'].max()}")
        print(f"⏱️  Resolve time range: {df['Resolve time'].min():.1f} to {df['Resolve time'].max():.1f} minutes")
        print(f"👥 Assignment groups: {df['Assignment group'].nunique()}")
        print(f"🎯 Native SLA Compliance: {df['sla_met_native'].sum()}/{len(df)} = {(df['sla_met_native'].sum()/len(df)*100):.1f}%")
        print(f"📊 MTTR-based SLA (240min): {df['sla_met_mttr'].sum()}/{len(df)} = {(df['sla_met_mttr'].sum()/len(df)*100):.1f}%")
        print(f"🎯 Goal SLA (180min): {df['sla_met_goal'].sum()}/{len(df)} = {(df['sla_met_goal'].sum()/len(df)*100):.1f}%")
        
        return df
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None

def calculate_sla_compliance_example():
    """
    Demonstrates SLA compliance calculation with sample data
    """
    print("="*60)
    print("SLA Compliance Calculation Logic")
    print("="*60)
    
    # Sample incident data with various MTTR values
    sample_data = {
        'ticket_id': ['INC001', 'INC002', 'INC003', 'INC004', 'INC005', 'INC006', 'INC007', 'INC008'],
        'created_at': [
            '2025-02-03 09:00:00',  # Monday (weekday)
            '2025-02-04 14:30:00',  # Tuesday (weekday)
            '2025-02-05 08:15:00',  # Wednesday (weekday)
            '2025-02-06 16:45:00',  # Thursday (weekday)
            '2025-02-07 11:20:00',  # Friday (weekday)
            '2025-02-10 09:00:00',  # Monday (weekday)
            '2025-02-11 10:00:00',  # Tuesday (weekday)
            '2025-02-12 15:00:00'   # Wednesday (weekday)
        ],
        'resolved_at': [
            '2025-02-03 10:30:00',  # 90 minutes (SLA MET)
            '2025-02-04 16:45:00',  # 135 minutes (SLA NOT MET)
            '2025-02-05 10:00:00',  # 105 minutes (SLA MET)
            '2025-02-07 09:15:00',  # 990 minutes (SLA NOT MET)
            '2025-02-07 13:20:00',  # 120 minutes exactly (SLA MET)
            '2025-02-10 11:30:00',  # 150 minutes (SLA NOT MET)
            '2025-02-11 11:45:00',  # 105 minutes (SLA MET)
            '2025-02-12 16:00:00'   # 60 minutes (SLA MET)
        ]
    }
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    # Convert to datetime
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['resolved_at'] = pd.to_datetime(df['resolved_at'])
    
    # Add weekday flag - exclude weekends from MTTR calculation (consistent with MTTR.py)
    df['created_weekday'] = df['created_at'].dt.dayofweek
    df['is_weekday_created'] = df['created_weekday'] < 5  # Monday-Friday only
    
    # Calculate MTTR: resolved_at minus created_at (in minutes)
    df['mttr_minutes'] = (df['resolved_at'] - df['created_at']).dt.total_seconds() / 60
    df['mttr_hours'] = df['mttr_minutes'] / 60
    
    print("Sample Data:")
    print(df[['ticket_id', 'created_at', 'resolved_at', 'mttr_minutes']].to_string(index=False))
    print("\n" + "="*60)
    
    # SLA Threshold
    SLA_THRESHOLD_MINUTES = 120  # 2 hours
    
    # Calculate SLA compliance for each incident
    df['sla_met'] = df['mttr_minutes'] <= SLA_THRESHOLD_MINUTES
    
    print("SLA Compliance Calculation:")
    print(f"SLA Threshold: {SLA_THRESHOLD_MINUTES} minutes ({SLA_THRESHOLD_MINUTES/60} hours)")
    print("-" * 50)
    
    for i, row in df.iterrows():
        status = "SLA MET" if row['sla_met'] else "SLA NOT MET"
        comparison = "<=" if row['sla_met'] else ">"
        print(f"{row['ticket_id']}: {row['mttr_minutes']:.0f} mins {comparison} {SLA_THRESHOLD_MINUTES} mins → {status}")
    
    print("\n" + "="*60)
    
    # Calculate overall SLA compliance rate
    total_incidents = len(df)
    sla_met_count = df['sla_met'].sum()
    sla_compliance_rate = (sla_met_count / total_incidents) * 100
    
    print("SLA Compliance Summary:")
    print(f"Total incidents: {total_incidents}")
    print(f"SLA met: {sla_met_count}")
    print(f"SLA not met: {total_incidents - sla_met_count}")
    print(f"SLA Compliance Rate: {sla_compliance_rate:.1f}%")
    
    # Breakdown by SLA status
    print(f"\nDetailed Breakdown:")
    sla_met_incidents = df[df['sla_met']]['ticket_id'].tolist()
    sla_not_met_incidents = df[~df['sla_met']]['ticket_id'].tolist()
    
    print(f"SLA Met ({len(sla_met_incidents)}): {', '.join(sla_met_incidents)}")
    print(f"SLA Not Met ({len(sla_not_met_incidents)}): {', '.join(sla_not_met_incidents)}")
    
    return df

def monthly_sla_compliance(df):
    """
    Demonstrates how SLA compliance is calculated by month
    """
    print("\n" + "="*60)
    print("Monthly SLA Compliance Calculation")
    print("="*60)
    
    # SLA Threshold
    SLA_THRESHOLD_MINUTES = 120
    
    # Group by month and calculate SLA compliance
    df['month'] = df['created_at'].dt.to_period('M')
    monthly_sla = df.groupby('month').agg({
        'ticket_id': 'count',
        'sla_met': ['sum', 'mean']
    }).round(3)
    
    # Flatten column names
    monthly_sla.columns = ['incident_count', 'sla_met_count', 'sla_compliance_rate']
    monthly_sla['sla_compliance_percentage'] = monthly_sla['sla_compliance_rate'] * 100
    monthly_sla['sla_not_met_count'] = monthly_sla['incident_count'] - monthly_sla['sla_met_count']
    
    print("Monthly SLA Compliance Breakdown:")
    print(monthly_sla[['incident_count', 'sla_met_count', 'sla_not_met_count', 'sla_compliance_percentage']].to_string())
    
    return monthly_sla

def team_sla_compliance(df):
    """
    Demonstrates how SLA compliance is calculated by team
    """
    print("\n" + "="*60)
    print("Team SLA Compliance Calculation")
    print("="*60)
    
    # Add sample team assignments
    df['assignment_group'] = ['Team A', 'Team B', 'Team A', 'Team C', 'Team B', 'Team A', 'Team C', 'Team D']
    
    # SLA Threshold
    SLA_THRESHOLD_MINUTES = 120
    
    # Group by team and calculate SLA compliance
    team_sla = df.groupby('assignment_group').agg({
        'ticket_id': 'count',
        'sla_met': ['sum', 'mean'],
        'mttr_minutes': 'mean'
    }).round(2)
    
    # Flatten column names
    team_sla.columns = ['incident_count', 'sla_met_count', 'sla_compliance_rate', 'avg_mttr_minutes']
    team_sla['sla_compliance_percentage'] = team_sla['sla_compliance_rate'] * 100
    team_sla['sla_not_met_count'] = team_sla['incident_count'] - team_sla['sla_met_count']
    team_sla['avg_mttr_hours'] = team_sla['avg_mttr_minutes'] / 60
    
    print("Team SLA Compliance Breakdown:")
    print(team_sla[['incident_count', 'sla_met_count', 'sla_not_met_count', 'sla_compliance_percentage', 'avg_mttr_hours']].to_string())
    
    return team_sla

def quarterly_sla_compliance(df):
    """
    Demonstrates how SLA compliance works with quarterly filtering
    """
    print("\n" + "="*60)
    print("Quarterly SLA Compliance Calculation")
    print("="*60)
    
    # SLA Threshold
    SLA_THRESHOLD_MINUTES = 120
    
    # Simulate quarterly filtering (like in dashboard)
    print("Quarterly Breakdown:")
    
    # All data
    total_incidents = len(df)
    sla_met_all = df['sla_met'].sum()
    sla_rate_all = (sla_met_all / total_incidents) * 100
    print(f"All Data: {sla_met_all}/{total_incidents} = {sla_rate_all:.1f}% SLA compliance")
    
    # Filter by month to simulate quarterly filtering
    q1_months = [2]  # February (simplified for demo)
    q2_months = [2]  # February (all our demo data is in Feb)
    
    q1_df = df[df['created_at'].dt.month.isin(q1_months)]
    if len(q1_df) > 0:
        q1_sla_met = q1_df['sla_met'].sum()
        q1_total = len(q1_df)
        q1_rate = (q1_sla_met / q1_total) * 100
        print(f"Q1 (Feb): {q1_sla_met}/{q1_total} = {q1_rate:.1f}% SLA compliance")
    
    return df

def dashboard_implementation_notes():
    """
    Shows how SLA compliance logic is implemented in the actual dashboard
    """
    print("\n" + "="*60)
    print("Dashboard Implementation Notes")
    print("="*60)
    
    implementation_code = '''
# In app.py - Data Loading:
# SLA compliance would be calculated from MTTR_calculated
SLA_THRESHOLD_MINUTES = 120  # 2 hours
incidents_df['sla_met_mttr'] = incidents_df['MTTR_calculated'] <= SLA_THRESHOLD_MINUTES

# In app.py - Overview API:
# Current implementation uses 'Made SLA' column from Excel data
sla_compliance = (filtered_df['Made SLA'] == True).sum() / total_incidents * 100

# Alternative implementation based on MTTR:
# sla_compliance_mttr = (filtered_df['MTTR_calculated'] <= 120).sum() / total_incidents * 100

# In app.py - Monthly Trends:
monthly_data = df.groupby(df['Created'].dt.to_period('M')).agg({
    'Number': 'count',
    'MTTR_calculated': lambda x: df.loc[x.index, 'MTTR_calculated'][df.loc[x.index, 'is_weekday_created']].mean(),
    'Reopen count': lambda x: (x == 0).sum() / len(x) * 100,
    'sla_met_mttr': lambda x: (df.loc[x.index, 'MTTR_calculated'] <= 120).sum() / len(x) * 100  # SLA compliance
}).round(2)

# In app.py - Team Performance:
team_stats = filtered_df.groupby('Assignment group').agg({
    'Number': 'count',
    'MTTR_calculated': lambda x: filtered_df.loc[x.index, 'MTTR_calculated'][filtered_df.loc[x.index, 'is_weekday_created']].mean(),
    'Reopen count': lambda x: (x == 0).sum() / len(x) * 100,
    'sla_met_mttr': lambda x: (filtered_df.loc[x.index, 'MTTR_calculated'] <= 120).sum() / len(x) * 100  # SLA compliance
}).round(2)
    '''
    
    print("Code Implementation for MTTR-based SLA:")
    print(implementation_code)
    
    print("\nKey Points:")
    print("- SLA threshold: 120 minutes (2 hours)")
    print("- SLA Met: MTTR <= 120 minutes")
    print("- SLA Not Met: MTTR > 120 minutes")
    print("- Calculation: (SLA Met Count / Total Incidents) × 100")
    print("- Current dashboard uses 'Made SLA' column from Excel data")
    print("- Alternative: Calculate SLA compliance directly from MTTR values")
    print("- Weekend exclusion applies to MTTR calculation, affecting SLA compliance")

def sla_compliance_edge_cases():
    """
    Demonstrates edge cases and special scenarios
    """
    print("\n" + "="*60)
    print("SLA Compliance Edge Cases")
    print("="*60)
    
    edge_cases = {
        'scenario': [
            'Exactly at threshold',
            'Just under threshold',
            'Just over threshold',
            'Very fast resolution',
            'Very slow resolution',
            'Weekend created (excluded from MTTR)',
            'Missing resolution time'
        ],
        'mttr_minutes': [120, 119, 121, 15, 480, 90, None],
        'created_day': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Monday'],
        'sla_met': [True, True, False, True, False, 'N/A (weekend)', 'N/A (missing)']
    }
    
    edge_df = pd.DataFrame(edge_cases)
    
    print("Edge Case Scenarios:")
    print(edge_df.to_string(index=False))
    
    print(f"\nSLA Logic:")
    print(f"- MTTR = 120 minutes exactly → SLA MET (using <= comparison)")
    print(f"- MTTR = 119 minutes → SLA MET")
    print(f"- MTTR = 121 minutes → SLA NOT MET")
    print(f"- Weekend incidents → Excluded from MTTR calculation")
    print(f"- Missing resolution → Cannot determine SLA compliance")

def analyze_real_data():
    """
    Analyze SLA compliance using the actual Combined_Incidents_Report_Feb_to_June_2025.xlsx data
    """
    df = load_new_incident_data()
    if df is None:
        print("❌ Cannot proceed without data")
        return
    
    print("\n" + "="*60)
    print("🔍 REAL DATA SLA COMPLIANCE ANALYSIS")
    print("="*60)
    
    # Calculate SLA compliance metrics
    total_incidents = len(df)
    
    # Native SLA (from Made SLA column)
    native_sla_met = df['sla_met_native'].sum()
    native_sla_rate = (native_sla_met / total_incidents) * 100
    
    # MTTR-based SLA (240 minutes)
    mttr_sla_met = df['sla_met_mttr'].sum()
    mttr_sla_rate = (mttr_sla_met / total_incidents) * 100
    
    # Goal SLA (180 minutes)
    goal_sla_met = df['sla_met_goal'].sum()
    goal_sla_rate = (goal_sla_met / total_incidents) * 100
    
    print(f"📊 OVERALL SLA COMPLIANCE METRICS:")
    print(f"   Total Incidents: {total_incidents:,}")
    print()
    print(f"   🎯 NATIVE SLA (Made SLA field): {native_sla_met:,}/{total_incidents:,} = {native_sla_rate:.1f}%")
    print(f"   📊 MTTR-based SLA (≤240min): {mttr_sla_met:,}/{total_incidents:,} = {mttr_sla_rate:.1f}%")
    print(f"   🏆 Goal SLA (≤180min): {goal_sla_met:,}/{total_incidents:,} = {goal_sla_rate:.1f}%")
    
    # Monthly breakdown
    print(f"\n📅 MONTHLY SLA COMPLIANCE BREAKDOWN:")
    df['created_month'] = df['Created'].dt.to_period('M')
    monthly_sla = df.groupby('created_month').agg({
        'Number': 'count',
        'sla_met_native': 'sum',
        'sla_met_mttr': 'sum',
        'sla_met_goal': 'sum'
    })
    monthly_sla['native_rate'] = (monthly_sla['sla_met_native'] / monthly_sla['Number'] * 100).round(1)
    monthly_sla['mttr_rate'] = (monthly_sla['sla_met_mttr'] / monthly_sla['Number'] * 100).round(1)
    monthly_sla['goal_rate'] = (monthly_sla['sla_met_goal'] / monthly_sla['Number'] * 100).round(1)
    
    for month, row in monthly_sla.iterrows():
        print(f"   {month}: {row['Number']:,} incidents")
        print(f"      Native SLA: {row['native_rate']:.1f}%, MTTR SLA: {row['mttr_rate']:.1f}%, Goal SLA: {row['goal_rate']:.1f}%")
    
    # Top/Bottom performing teams by MTTR-based SLA
    print(f"\n👥 TEAM SLA PERFORMANCE (MTTR-based ≤240min):")
    team_sla = df.groupby('Assignment group').agg({
        'Number': 'count',
        'sla_met_native': 'sum',
        'sla_met_mttr': 'sum',
        'sla_met_goal': 'sum'
    })
    team_sla['native_rate'] = (team_sla['sla_met_native'] / team_sla['Number'] * 100).round(1)
    team_sla['mttr_rate'] = (team_sla['sla_met_mttr'] / team_sla['Number'] * 100).round(1)
    team_sla['goal_rate'] = (team_sla['sla_met_goal'] / team_sla['Number'] * 100).round(1)
    team_sla = team_sla.sort_values('mttr_rate', ascending=False)
    
    print("   🏆 TOP 5 TEAMS (Highest MTTR-based SLA Compliance):")
    for team, row in team_sla.head(5).iterrows():
        print(f"      {team}: {row['mttr_rate']:.1f}% ({row['Number']:,} incidents)")
        print(f"         Native: {row['native_rate']:.1f}%, Goal: {row['goal_rate']:.1f}%")
    
    print("   ⚠️  BOTTOM 5 TEAMS (Lowest MTTR-based SLA Compliance):")
    for team, row in team_sla.tail(5).iterrows():
        print(f"      {team}: {row['mttr_rate']:.1f}% ({row['Number']:,} incidents)")
        print(f"         Native: {row['native_rate']:.1f}%, Goal: {row['goal_rate']:.1f}%")
    
    # Quarter comparison
    print(f"\n📈 QUARTERLY COMPARISON:")
    df['quarter'] = df['Created'].dt.month.map(lambda x: 'Q1' if x in [2,3,4] else 'Q2' if x in [5,6] else 'Other')
    quarter_sla = df.groupby('quarter').agg({
        'Number': 'count',
        'sla_met_native': 'sum',
        'sla_met_mttr': 'sum',
        'sla_met_goal': 'sum'
    })
    quarter_sla['native_rate'] = (quarter_sla['sla_met_native'] / quarter_sla['Number'] * 100).round(1)
    quarter_sla['mttr_rate'] = (quarter_sla['sla_met_mttr'] / quarter_sla['Number'] * 100).round(1)
    quarter_sla['goal_rate'] = (quarter_sla['sla_met_goal'] / quarter_sla['Number'] * 100).round(1)
    
    for quarter, row in quarter_sla.iterrows():
        if quarter != 'Other':
            print(f"   {quarter}: {row['Number']:,} incidents")
            print(f"      Native SLA: {row['native_rate']:.1f}%, MTTR SLA: {row['mttr_rate']:.1f}%, Goal SLA: {row['goal_rate']:.1f}%")
    
    return df

if __name__ == "__main__":
    print("🎯 SLA Compliance Analysis")
    print("📁 Using: Combined_Incidents_Report_Feb_to_June_2025.xlsx")
    
    # Run real data analysis first
    real_df = analyze_real_data()
    
    # Then run the demonstration with sample data
    print("\n" + "="*60)
    print("📚 DEMONSTRATION WITH SAMPLE DATA")
    print("="*60)
    df = calculate_sla_compliance_example()
    monthly_sla_compliance(df)
    team_sla_compliance(df)
    quarterly_sla_compliance(df)
    sla_compliance_edge_cases()
    dashboard_implementation_notes()
    
    print("\n" + "="*60)
    print("✅ SLA Compliance Analysis Complete!")
    print("Shows multiple SLA metrics: Native (Made SLA), MTTR-based, and Goal SLA.")
    print("Dashboard uses Native SLA as primary metric with MTTR-based as secondary.")
    print("="*60) 