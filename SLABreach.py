"""
SLA Breach Calculation Logic
===========================

Updated for: Combined_Incidents_Report_Feb_to_June_2025.xlsx

SLA Breach Metric Definition:
- Name: Total incidents with SLA breach
- Purpose: Count of tickets not meeting promised timelines  
- Units: Count
- Data Source: Combined_Incidents_Report_Feb_to_June_2025.xlsx with Created/Resolved timestamps
- Formula: count(MTTR > SLA Promised Minutes)
- SLA Promise: 240 minutes (4 hours) default for all incidents
- Delight Index Metrics: Used for measuring service quality

This file demonstrates SLA breach calculation logic using the new Excel data.
Note: 'Created' = opened_at and 'Resolved' = resolved_at, using 240min SLA promise
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
        
        # SLA Breach calculation: incidents exceeding promised timelines
        DEFAULT_SLA_PROMISE_MINUTES = 240  # 4 hours for all incidents
        df['sla_promised_minutes'] = DEFAULT_SLA_PROMISE_MINUTES
        df['sla_breached'] = df['MTTR_calculated'] > df['sla_promised_minutes']
        df['sla_variance_minutes'] = df['MTTR_calculated'] - df['sla_promised_minutes']
        
        print(f"✅ Data loaded successfully: {len(df)} incidents")
        print(f"📅 Date range: {df['Created'].min()} to {df['Created'].max()}")
        print(f"⏱️  MTTR range: {df['MTTR_calculated'].min():.1f} to {df['MTTR_calculated'].max():.1f} minutes")
        print(f"👥 Assignment groups: {df['Assignment group'].nunique()}")
        print(f"🔴 SLA Breaches: {df['sla_breached'].sum()}/{len(df)} = {(df['sla_breached'].sum()/len(df)*100):.1f}%")
        print(f"🎯 SLA Promise: {DEFAULT_SLA_PROMISE_MINUTES} minutes (4 hours) for all incidents")
        
        return df
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None

def calculate_sla_breach_example():
    """
    Demonstrates SLA breach calculation with sample data using various SLA thresholds
    """
    print("="*70)
    print("SLA Breach Calculation Logic")
    print("="*70)
    
    # Sample incident data with various resolution times and SLA promises
    sample_data = {
        'ticket_id': ['INC001', 'INC002', 'INC003', 'INC004', 'INC005', 'INC006', 'INC007', 'INC008', 'INC009', 'INC010'],
        'opened_at': [
            '2025-02-03 09:00:00',  # Monday
            '2025-02-04 14:30:00',  # Tuesday  
            '2025-02-05 08:15:00',  # Wednesday
            '2025-02-06 16:45:00',  # Thursday
            '2025-02-07 11:20:00',  # Friday
            '2025-02-10 09:00:00',  # Monday
            '2025-02-11 10:00:00',  # Tuesday
            '2025-02-12 15:00:00',  # Wednesday
            '2025-02-13 08:30:00',  # Thursday
            '2025-02-14 12:00:00'   # Friday
        ],
        'resolved_at': [
            '2025-02-03 10:30:00',  # 90 minutes
            '2025-02-04 16:45:00',  # 135 minutes
            '2025-02-05 10:00:00',  # 105 minutes
            '2025-02-07 09:15:00',  # 990 minutes (16.5 hours)
            '2025-02-07 13:20:00',  # 120 minutes exactly
            '2025-02-10 12:00:00',  # 180 minutes (3 hours)
            '2025-02-11 11:45:00',  # 105 minutes
            '2025-02-12 18:00:00',  # 180 minutes (3 hours)
            '2025-02-13 10:30:00',  # 120 minutes exactly
            '2025-02-14 16:00:00'   # 240 minutes (4 hours)
        ],
        'priority': ['P1', 'P2', 'P3', 'P1', 'P2', 'P3', 'P1', 'P2', 'P3', 'P1'],
        'assignment_group': ['DGTC', 'Homeoffice', 'JST', 'Sunnyvale', 'DGTC', 'Homeoffice', 'JST', 'Sunnyvale', 'DGTC', 'Homeoffice']
    }
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    # Convert to datetime
    df['opened_at'] = pd.to_datetime(df['opened_at'])
    df['resolved_at'] = pd.to_datetime(df['resolved_at'])
    
    # Calculate actual resolution time in minutes
    df['actual_resolution_time_minutes'] = (df['resolved_at'] - df['opened_at']).dt.total_seconds() / 60
    df['actual_resolution_time_hours'] = df['actual_resolution_time_minutes'] / 60
    
    # Define SLA promises by priority (in minutes)
    sla_promises = {
        'P1': 120,   # 2 hours for critical incidents
        'P2': 240,   # 4 hours for high priority
        'P3': 480    # 8 hours for normal priority
    }
    
    # Assign SLA promised time based on priority
    df['sla_promised_minutes'] = df['priority'].map(sla_promises)
    df['sla_promised_hours'] = df['sla_promised_minutes'] / 60
    
    print("Sample Data with SLA Promises:")
    display_cols = ['ticket_id', 'priority', 'opened_at', 'resolved_at', 'actual_resolution_time_minutes', 'sla_promised_minutes']
    print(df[display_cols].to_string(index=False, max_colwidth=20))
    print("\n" + "="*70)
    
    # Calculate SLA breach: actual_time > promised_time
    df['sla_breached'] = df['actual_resolution_time_minutes'] > df['sla_promised_minutes']
    df['sla_variance_minutes'] = df['actual_resolution_time_minutes'] - df['sla_promised_minutes']
    
    print("SLA Breach Analysis:")
    print("Formula: count((resolved_at minus opened_at) > SLA Promised)")
    print("-" * 70)
    
    for i, row in df.iterrows():
        breach_status = "🔴 SLA BREACH" if row['sla_breached'] else "🟢 SLA MET"
        comparison = ">" if row['sla_breached'] else "<="
        variance = f"(+{row['sla_variance_minutes']:.0f} min over)" if row['sla_breached'] else f"({abs(row['sla_variance_minutes']):.0f} min under)"
        
        print(f"{row['ticket_id']} ({row['priority']}): {row['actual_resolution_time_minutes']:.0f} min {comparison} {row['sla_promised_minutes']:.0f} min → {breach_status} {variance}")
    
    print("\n" + "="*70)
    
    # Calculate SLA breach metrics
    total_incidents = len(df)
    sla_breaches = df['sla_breached'].sum()
    sla_met = total_incidents - sla_breaches
    breach_rate = (sla_breaches / total_incidents) * 100
    compliance_rate = (sla_met / total_incidents) * 100
    
    print("SLA Breach Summary:")
    print(f"Total Incidents: {total_incidents}")
    print(f"SLA Breaches: {sla_breaches}")
    print(f"SLA Met: {sla_met}")
    print(f"Breach Rate: {breach_rate:.1f}%")
    print(f"Compliance Rate: {compliance_rate:.1f}%")
    
    # Breakdown by breach status
    print(f"\nDetailed Breakdown:")
    breached_incidents = df[df['sla_breached']]['ticket_id'].tolist()
    met_incidents = df[~df['sla_breached']]['ticket_id'].tolist()
    
    print(f"SLA Breached ({len(breached_incidents)}): {', '.join(breached_incidents)}")
    print(f"SLA Met ({len(met_incidents)}): {', '.join(met_incidents)}")
    
    # Priority breakdown
    print(f"\nSLA Breach by Priority:")
    priority_breach = df.groupby('priority').agg({
        'ticket_id': 'count',
        'sla_breached': ['sum', 'mean']
    }).round(3)
    priority_breach.columns = ['total_incidents', 'breach_count', 'breach_rate']
    priority_breach['breach_percentage'] = priority_breach['breach_rate'] * 100
    priority_breach['sla_promise_hours'] = priority_breach.index.map(lambda x: sla_promises[x] / 60)
    
    print(priority_breach[['total_incidents', 'breach_count', 'breach_percentage', 'sla_promise_hours']].to_string())
    
    return df

def monthly_sla_breach_analysis(df):
    """
    Demonstrates how SLA breach analysis works by month
    """
    print("\n" + "="*70)
    print("Monthly SLA Breach Analysis")
    print("="*70)
    
    # Group by month and calculate SLA breach metrics
    df['month'] = df['opened_at'].dt.to_period('M')
    monthly_breach = df.groupby('month').agg({
        'ticket_id': 'count',
        'sla_breached': ['sum', 'mean'],
        'sla_variance_minutes': lambda x: df.loc[x.index, 'sla_variance_minutes'][df.loc[x.index, 'sla_breached']].mean()
    }).round(2)
    
    # Flatten column names
    monthly_breach.columns = ['total_incidents', 'breach_count', 'breach_rate', 'avg_breach_variance_minutes']
    monthly_breach['breach_percentage'] = monthly_breach['breach_rate'] * 100
    monthly_breach['compliance_percentage'] = 100 - monthly_breach['breach_percentage']
    monthly_breach['met_count'] = monthly_breach['total_incidents'] - monthly_breach['breach_count']
    
    print("Monthly SLA Breach Breakdown:")
    display_cols = ['total_incidents', 'breach_count', 'met_count', 'breach_percentage', 'compliance_percentage']
    print(monthly_breach[display_cols].to_string())
    
    print(f"\nMonthly Detailed Analysis:")
    for month in df['month'].unique():
        month_data = df[df['month'] == month]
        total = len(month_data)
        breaches = month_data['sla_breached'].sum()
        breach_pct = (breaches / total) * 100
        print(f"{month}: {breaches}/{total} breaches = {breach_pct:.1f}% breach rate")
    
    return monthly_breach

def team_sla_breach_analysis(df):
    """
    Demonstrates SLA breach analysis by team/assignment group
    """
    print("\n" + "="*70)
    print("Team SLA Breach Analysis")
    print("="*70)
    
    # Group by team and calculate SLA breach metrics
    team_breach = df.groupby('assignment_group').agg({
        'ticket_id': 'count',
        'sla_breached': ['sum', 'mean'],
        'actual_resolution_time_minutes': 'mean',
        'sla_promised_minutes': 'mean',
        'sla_variance_minutes': lambda x: df.loc[x.index, 'sla_variance_minutes'][df.loc[x.index, 'sla_breached']].mean()
    }).round(2)
    
    # Flatten column names
    team_breach.columns = ['total_incidents', 'breach_count', 'breach_rate', 'avg_resolution_minutes', 'avg_sla_promise_minutes', 'avg_breach_variance_minutes']
    team_breach['breach_percentage'] = team_breach['breach_rate'] * 100
    team_breach['compliance_percentage'] = 100 - team_breach['breach_percentage']
    team_breach['met_count'] = team_breach['total_incidents'] - team_breach['breach_count']
    team_breach['avg_resolution_hours'] = team_breach['avg_resolution_minutes'] / 60
    
    print("Team SLA Breach Breakdown:")
    display_cols = ['total_incidents', 'breach_count', 'met_count', 'breach_percentage', 'avg_resolution_hours']
    print(team_breach[display_cols].to_string())
    
    return team_breach

def quarterly_sla_breach_analysis(df):
    """
    Demonstrates SLA breach analysis with quarterly filtering (like dashboard)
    """
    print("\n" + "="*70)
    print("Quarterly SLA Breach Analysis (Dashboard Integration)")
    print("="*70)
    
    # All data analysis
    total_incidents = len(df)
    total_breaches = df['sla_breached'].sum()
    total_breach_rate = (total_breaches / total_incidents) * 100
    print(f"All Data: {total_breaches}/{total_incidents} breaches = {total_breach_rate:.1f}% breach rate")
    
    # Simulate quarterly filtering
    # Q1: February, March, April (months 2, 3, 4)
    # Q2: May, June (months 5, 6)
    
    q1_df = df[df['opened_at'].dt.month.isin([2, 3, 4])]
    if len(q1_df) > 0:
        q1_breaches = q1_df['sla_breached'].sum()
        q1_total = len(q1_df)
        q1_breach_rate = (q1_breaches / q1_total) * 100
        print(f"Q1 (Feb-Apr): {q1_breaches}/{q1_total} breaches = {q1_breach_rate:.1f}% breach rate")
    
    q2_df = df[df['opened_at'].dt.month.isin([5, 6])]
    if len(q2_df) > 0:
        q2_breaches = q2_df['sla_breached'].sum()
        q2_total = len(q2_df)
        q2_breach_rate = (q2_breaches / q2_total) * 100
        print(f"Q2 (May-Jun): {q2_breaches}/{q2_total} breaches = {q2_breach_rate:.1f}% breach rate")
    else:
        print("Q2 (May-Jun): No data available in sample")
    
    return df

def sla_breach_vs_compliance_comparison():
    """
    Compare SLA breach approach vs current SLA compliance approach
    """
    print("\n" + "="*70)
    print("SLA Breach vs SLA Compliance Comparison")
    print("="*70)
    
    comparison_data = {
        'Metric': ['SLA Breach (Proposed)', 'SLA Compliance (Current)'],
        'Logic': [
            'count((resolved_at - opened_at) > SLA_Promised)',
            'count((resolved_at - opened_at) <= 120_minutes)'
        ],
        'Focus': [
            'Incidents NOT meeting promised timelines',
            'Incidents meeting fixed 120-min threshold'
        ],
        'Threshold': [
            'Variable by priority (P1=2h, P2=4h, P3=8h)',
            'Fixed 120 minutes (2 hours) for all'
        ],
        'Unit': ['Count of breached incidents', 'Percentage of compliant incidents'],
        'Purpose': ['Identify service quality issues', 'Overall performance tracking']
    }
    
    comparison_df = pd.DataFrame(comparison_data)
    print(comparison_df.to_string(index=False, max_colwidth=50))
    
    print(f"\nKey Differences:")
    print(f"1. SLA Breach uses VARIABLE thresholds based on incident priority")
    print(f"2. SLA Breach counts FAILURES (incidents exceeding promise)")
    print(f"3. SLA Compliance uses FIXED threshold (120 minutes)")  
    print(f"4. SLA Compliance measures SUCCESS rate (percentage)")
    print(f"5. Both can be implemented simultaneously for comprehensive monitoring")

def dashboard_integration_notes():
    """
    Shows how SLA breach logic could be integrated into the dashboard
    """
    print("\n" + "="*70)
    print("Dashboard Integration Implementation Notes")
    print("="*70)
    
    implementation_code = '''
# In app.py - Data Loading (add SLA breach calculation):

# Define SLA promises by priority (in minutes)
SLA_PROMISES = {
    'P1': 120,   # 2 hours for critical incidents
    'P2': 240,   # 4 hours for high priority  
    'P3': 480,   # 8 hours for normal priority
    'default': 240  # Default for missing priority
}

# Add priority-based SLA promises (if Priority column exists)
if 'Priority' in incidents_df.columns:
    incidents_df['sla_promised_minutes'] = incidents_df['Priority'].map(SLA_PROMISES).fillna(SLA_PROMISES['default'])
else:
    # Use default SLA promise if no priority column
    incidents_df['sla_promised_minutes'] = SLA_PROMISES['default']

# Calculate SLA breach: actual_time > promised_time
incidents_df['actual_resolution_minutes'] = (incidents_df['Resolved'] - incidents_df['Created']).dt.total_seconds() / 60
incidents_df['sla_breached'] = incidents_df['actual_resolution_minutes'] > incidents_df['sla_promised_minutes']
incidents_df['sla_variance_minutes'] = incidents_df['actual_resolution_minutes'] - incidents_df['sla_promised_minutes']

# In app.py - Overview API (add SLA breach metrics):
sla_breaches = (filtered_df['sla_breached'] == True).sum()
sla_breach_rate = (sla_breaches / total_incidents) * 100 if total_incidents > 0 else 0

return jsonify({
    # ... existing metrics ...
    'sla_breaches': sla_breaches,
    'sla_breach_rate': round(sla_breach_rate, 1),
    'sla_compliance_rate': round(100 - sla_breach_rate, 1)  # Inverse of breach rate
})

# In app.py - Monthly Trends (add SLA breach tracking):
monthly_data = df.groupby(df['Created'].dt.to_period('M')).agg({
    'Number': 'count',
    'MTTR_calculated': lambda x: df.loc[x.index, 'MTTR_calculated'][df.loc[x.index, 'is_weekday_created']].mean(),
    'Reopen count': lambda x: (x == 0).sum() / len(x) * 100,
    'sla_breached': lambda x: (df.loc[x.index, 'sla_breached']).sum(),  # Count of breaches per month
    'sla_breach_rate': lambda x: (df.loc[x.index, 'sla_breached']).sum() / len(x) * 100  # Breach rate per month
}).round(2)

# In app.py - Team Performance (add SLA breach by team):
team_stats = filtered_df.groupby('Assignment group').agg({
    'Number': 'count',
    'MTTR_calculated': lambda x: filtered_df.loc[x.index, 'MTTR_calculated'][filtered_df.loc[x.index, 'is_weekday_created']].mean(),
    'Reopen count': lambda x: (x == 0).sum() / len(x) * 100,
    'sla_breached': lambda x: (filtered_df.loc[x.index, 'sla_breached']).sum(),  # Breach count per team
    'sla_breach_rate': lambda x: (filtered_df.loc[x.index, 'sla_breached']).sum() / len(x) * 100  # Breach rate per team
}).round(2)

# New API endpoint for SLA breach analysis:
@app.route('/api/sla_breach')
def api_sla_breach():
    # Return detailed SLA breach analysis
    # Including breach count, breach rate, worst performing teams, etc.
    pass
    '''
    
    print("Code Implementation for SLA Breach Tracking:")
    print(implementation_code)
    
    print("\nDashboard UI Integration:")
    print("1. Add 'SLA Breaches' metric card showing total breach count")
    print("2. Add 'Breach Rate' percentage alongside compliance rate") 
    print("3. Create SLA breach trend chart showing monthly breach counts")
    print("4. Add breach count column to team performance table")
    print("5. Implement breach severity indicator (red for high breach rates)")
    print("6. Add drill-down capability to view individual breached tickets")

def sla_breach_edge_cases():
    """
    Demonstrates edge cases and special scenarios for SLA breach calculation
    """
    print("\n" + "="*70)
    print("SLA Breach Edge Cases")
    print("="*70)
    
    edge_cases = {
        'scenario': [
            'Exactly at promise time',
            'Just under promise time', 
            'Just over promise time',
            'Very fast resolution',
            'Severe breach (3x promise)',
            'Missing priority (use default)',
            'Weekend created incident',
            'Missing resolution time'
        ],
        'actual_minutes': [120, 119, 121, 15, 360, 180, 90, None],
        'promised_minutes': [120, 120, 120, 120, 120, 240, 120, 120],
        'priority': ['P1', 'P1', 'P1', 'P1', 'P1', None, 'P1', 'P1'],
        'sla_breached': [False, False, True, False, True, False, False, 'N/A (missing)'],
        'variance': [0, -1, 1, -105, 240, -60, -30, 'N/A']
    }
    
    edge_df = pd.DataFrame(edge_cases)
    
    print("Edge Case Scenarios:")
    print(edge_df.to_string(index=False))
    
    print(f"\nSLA Breach Logic:")
    print(f"- actual_time = 120 min, promise = 120 min → NO BREACH (using > comparison)")
    print(f"- actual_time = 119 min, promise = 120 min → NO BREACH")  
    print(f"- actual_time = 121 min, promise = 120 min → SLA BREACH")
    print(f"- Missing priority → Use default SLA promise (240 min)")
    print(f"- Weekend incidents → Still subject to SLA promises")
    print(f"- Missing resolution → Cannot determine breach status")
    print(f"- Severe breaches (>2x promise) → Flag for escalation")

def real_world_application_example():
    """
    Show how this would work with real dashboard data structure
    """
    print("\n" + "="*70)
    print("Real-World Application with Dashboard Data")
    print("="*70)
    
    # Simulate real dashboard data structure
    real_data = {
        'Number': ['INC0001234', 'INC0001235', 'INC0001236', 'INC0001237'],
        'Created': ['2025-02-15 09:30:00', '2025-02-15 14:15:00', '2025-02-16 08:00:00', '2025-02-16 16:30:00'],
        'Resolved': ['2025-02-15 11:45:00', '2025-02-15 18:30:00', '2025-02-16 12:00:00', '2025-02-17 10:30:00'],
        'Assignment group': ['DGTC', 'Homeoffice', 'JST', 'Sunnyvale'],
        'Priority': ['P1', 'P2', 'P3', 'P1']  # This column may or may not exist in real data
    }
    
    real_df = pd.DataFrame(real_data)
    real_df['Created'] = pd.to_datetime(real_df['Created'])
    real_df['Resolved'] = pd.to_datetime(real_df['Resolved'])
    
    # Apply SLA breach logic
    sla_promises = {'P1': 120, 'P2': 240, 'P3': 480}
    real_df['sla_promised_minutes'] = real_df['Priority'].map(sla_promises)
    real_df['actual_resolution_minutes'] = (real_df['Resolved'] - real_df['Created']).dt.total_seconds() / 60
    real_df['sla_breached'] = real_df['actual_resolution_minutes'] > real_df['sla_promised_minutes']
    
    print("Real Dashboard Data Example:")
    display_cols = ['Number', 'Assignment group', 'Priority', 'actual_resolution_minutes', 'sla_promised_minutes', 'sla_breached']
    print(real_df[display_cols].to_string(index=False))
    
    # Summary metrics for dashboard
    total_incidents = len(real_df) 
    total_breaches = real_df['sla_breached'].sum()
    breach_rate = (total_breaches / total_incidents) * 100
    
    print(f"\nDashboard Summary Metrics:")
    print(f"Total Incidents: {total_incidents}")
    print(f"SLA Breaches: {total_breaches}")
    print(f"Breach Rate: {breach_rate:.1f}%")
    print(f"Compliance Rate: {100-breach_rate:.1f}%")

def analyze_real_data():
    """
    Analyze SLA breaches using the actual Combined_Incidents_Report_Feb_to_June_2025.xlsx data
    """
    df = load_new_incident_data()
    if df is None:
        print("❌ Cannot proceed without data")
        return
    
    print("\n" + "="*70)
    print("🔍 REAL DATA SLA BREACH ANALYSIS")
    print("="*70)
    
    # Calculate SLA breach metrics
    total_incidents = len(df)
    total_breaches = df['sla_breached'].sum()
    breach_rate = (total_breaches / total_incidents) * 100
    compliance_rate = 100 - breach_rate
    
    # Calculate average variance for breached incidents
    breached_incidents = df[df['sla_breached']]
    avg_breach_variance = breached_incidents['sla_variance_minutes'].mean() if len(breached_incidents) > 0 else 0
    
    print(f"📊 OVERALL SLA BREACH METRICS:")
    print(f"   Total Incidents: {total_incidents:,}")
    print(f"   SLA Breaches: {total_breaches:,}")
    print(f"   SLA Met: {total_incidents - total_breaches:,}")
    print(f"   Breach Rate: {breach_rate:.1f}%")
    print(f"   Compliance Rate: {compliance_rate:.1f}%")
    print(f"   Avg Breach Variance: {avg_breach_variance:.1f} minutes ({avg_breach_variance/60:.1f} hours)")
    print(f"   SLA Promise: 240 minutes (4 hours) for all incidents")
    
    # Monthly breakdown
    print(f"\n📅 MONTHLY SLA BREACH BREAKDOWN:")
    df['created_month'] = df['Created'].dt.to_period('M')
    monthly_breach = df.groupby('created_month').agg({
        'Number': 'count',
        'sla_breached': ['sum', 'mean'],
        'sla_variance_minutes': lambda x: df.loc[x.index, 'sla_variance_minutes'][df.loc[x.index, 'sla_breached']].mean()
    }).round(1)
    monthly_breach.columns = ['incidents', 'breach_count', 'breach_rate', 'avg_breach_variance']
    monthly_breach['compliance_rate'] = (1 - monthly_breach['breach_rate']) * 100
    monthly_breach['breach_percentage'] = monthly_breach['breach_rate'] * 100
    
    for month, row in monthly_breach.iterrows():
        print(f"   {month}: {row['incidents']:,} incidents")
        print(f"      Breaches: {row['breach_count']:.0f} ({row['breach_percentage']:.1f}%)")
        print(f"      Compliance: {row['compliance_rate']:.1f}%")
        if not pd.isna(row['avg_breach_variance']):
            print(f"      Avg Breach Variance: {row['avg_breach_variance']:.1f} min")
    
    # Top/Bottom performing teams by breach rate
    print(f"\n👥 TEAM SLA BREACH PERFORMANCE:")
    team_breach = df.groupby('Assignment group').agg({
        'Number': 'count',
        'sla_breached': ['sum', 'mean'],
        'MTTR_calculated': 'mean',
        'sla_variance_minutes': lambda x: df.loc[x.index, 'sla_variance_minutes'][df.loc[x.index, 'sla_breached']].mean()
    }).round(1)
    team_breach.columns = ['incidents', 'breach_count', 'breach_rate', 'avg_mttr', 'avg_breach_variance']
    team_breach['breach_percentage'] = team_breach['breach_rate'] * 100
    team_breach['compliance_rate'] = (1 - team_breach['breach_rate']) * 100
    team_breach = team_breach.sort_values('breach_rate', ascending=False)
    
    print("   🔴 TOP 5 TEAMS (Highest Breach Rate):")
    for team, row in team_breach.head(5).iterrows():
        print(f"      {team}: {row['breach_percentage']:.1f}% breach rate ({row['breach_count']:.0f}/{row['incidents']:.0f})")
        print(f"         Avg MTTR: {row['avg_mttr']:.1f} min, Compliance: {row['compliance_rate']:.1f}%")
    
    print("   🟢 BOTTOM 5 TEAMS (Lowest Breach Rate):")
    for team, row in team_breach.tail(5).iterrows():
        print(f"      {team}: {row['breach_percentage']:.1f}% breach rate ({row['breach_count']:.0f}/{row['incidents']:.0f})")
        print(f"         Avg MTTR: {row['avg_mttr']:.1f} min, Compliance: {row['compliance_rate']:.1f}%")
    
    # Quarter comparison
    print(f"\n📈 QUARTERLY COMPARISON:")
    df['quarter'] = df['Created'].dt.month.map(lambda x: 'Q1' if x in [2,3,4] else 'Q2' if x in [5,6] else 'Other')
    quarter_breach = df.groupby('quarter').agg({
        'Number': 'count',
        'sla_breached': ['sum', 'mean']
    }).round(1)
    quarter_breach.columns = ['incidents', 'breach_count', 'breach_rate']
    quarter_breach['breach_percentage'] = quarter_breach['breach_rate'] * 100
    quarter_breach['compliance_rate'] = (1 - quarter_breach['breach_rate']) * 100
    
    for quarter, row in quarter_breach.iterrows():
        if quarter != 'Other':
            print(f"   {quarter}: {row['incidents']:.0f} incidents")
            print(f"      Breaches: {row['breach_count']:.0f} ({row['breach_percentage']:.1f}%)")
            print(f"      Compliance: {row['compliance_rate']:.1f}%")
    
    # Severe breach analysis (incidents >2x SLA promise)
    severe_breach_threshold = 480  # 2x the 240min promise
    severe_breaches = df[df['MTTR_calculated'] > severe_breach_threshold]
    print(f"\n⚠️  SEVERE BREACH ANALYSIS (>2x SLA Promise = >{severe_breach_threshold}min):")
    print(f"   Severe Breaches: {len(severe_breaches):,} ({len(severe_breaches)/total_incidents*100:.1f}%)")
    if len(severe_breaches) > 0:
        print(f"   Avg Time for Severe Breaches: {severe_breaches['MTTR_calculated'].mean():.1f} min")
        print(f"   Max Breach: {severe_breaches['MTTR_calculated'].max():.1f} min")
    
    return df

if __name__ == "__main__":
    print("🔴 SLA Breach Analysis")
    print("📁 Using: Combined_Incidents_Report_Feb_to_June_2025.xlsx")
    
    # Run real data analysis first
    real_df = analyze_real_data()
    
    # Then run the demonstration with sample data
    print("\n" + "="*70)
    print("📚 DEMONSTRATION WITH SAMPLE DATA")
    print("="*70)
    df = calculate_sla_breach_example()
    monthly_sla_breach_analysis(df)
    team_sla_breach_analysis(df)
    quarterly_sla_breach_analysis(df)
    sla_breach_vs_compliance_comparison()
    sla_breach_edge_cases()
    dashboard_integration_notes()
    real_world_application_example()
    
    print("\n" + "="*70)
    print("✅ SLA Breach Analysis Complete!")
    print("Shows incidents where MTTR > 240 minutes (4-hour SLA promise)")
    print("Can be integrated alongside existing SLA compliance metrics in dashboard.")
    print("="*70)
