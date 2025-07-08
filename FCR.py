"""
FCR (First Contact Resolution) Calculation Logic
===============================================

Updated for: Combined_Incidents_Report_Feb_to_June_2025.xlsx
Now includes improved handling of invalid/null reopen counts

P1 Metric Definition:
- Name: First Contact Resolution (FCR)
- Purpose: Measures How Many Tickets Were Solved on the First Try
- Units: Percent
- Data Source: Combined_Incidents_Report_Feb_to_June_2025.xlsx with Reopen count field
- Formula: (Number of Tickets Resolved on First Contact / Total Valid Tickets) x 100
- Logic: "First Contact" means Reopen count = 0
- Note: Invalid/null reopen counts are excluded from calculation

This file demonstrates the exact logic used in the dashboard application.
"""

import pandas as pd
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
        
        # Convert reopen count to numeric - handle non-numeric values
        df['Reopen count'] = pd.to_numeric(df['Reopen count'], errors='coerce')
        
        # Count invalid reopen counts
        invalid_count = df['Reopen count'].isna().sum()
        
        print(f"✅ Data loaded successfully: {len(df)} incidents")
        print(f"📅 Date range: {df['Created'].min()} to {df['Created'].max()}")
        print(f"🔄 Reopen count range: {df['Reopen count'].min():.0f} to {df['Reopen count'].max():.0f}")
        if invalid_count > 0:
            print(f"⚠️  Invalid reopen counts: {invalid_count} (will be excluded from FCR calculation)")
        print(f"👥 Assignment groups: {df['Assignment group'].nunique()}")
        
        return df
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return None

def calculate_fcr_with_validation(df):
    """
    Calculate FCR with proper handling of invalid data
    """
    # Separate incidents by reopen count status
    fcr_incidents = df[df['Reopen count'] == 0]
    non_fcr_incidents = df[df['Reopen count'] > 0]
    unknown_incidents = df[df['Reopen count'].isna()]
    
    fcr_count = len(fcr_incidents)
    non_fcr_count = len(non_fcr_incidents)
    unknown_count = len(unknown_incidents)
    
    # Calculate FCR percentage (excluding unknowns)
    valid_incidents = len(df) - unknown_count
    fcr_percentage = (fcr_count / valid_incidents * 100) if valid_incidents > 0 else 0
    
    return {
        'total_incidents': len(df),
        'fcr_count': fcr_count,
        'non_fcr_count': non_fcr_count,
        'unknown_count': unknown_count,
        'valid_incidents': valid_incidents,
        'fcr_percentage': fcr_percentage
    }

def calculate_fcr_example():
    """
    Demonstrates FCR calculation with sample data including edge cases
    """
    print("="*60)
    print("FCR (First Contact Resolution) Calculation Logic")
    print("="*60)
    
    # Sample incident data including invalid cases
    sample_data = {
        'ticket_id': ['INC001', 'INC002', 'INC003', 'INC004', 'INC005', 'INC006', 'INC007', 'INC008', 'INC009'],
        'Reopen count': [0, 1, 0, 0, 2, 0, 0, 1, np.nan],  # Including NaN
        'assignment_group': ['Team A', 'Team A', 'Team B', 'Team B', 'Team C', 'Team C', 'Team A', 'Team B', 'Team C'],
        'created_month': ['2025-02', '2025-02', '2025-02', '2025-03', '2025-03', '2025-03', '2025-03', '2025-03', '2025-03']
    }
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    print("Sample Data:")
    print(df.to_string(index=False))
    print("\n" + "="*60)
    
    # Calculate FCR with validation
    fcr_results = calculate_fcr_with_validation(df)
    
    print("FCR Calculation Breakdown:")
    print("Formula: (FCR Incidents / Valid Incidents) × 100")
    print("Where:")
    print("  - FCR Incident = reopen_count = 0")
    print("  - Valid Incident = reopen_count is not null/NaN")
    print("-" * 40)
    
    for i, row in df.iterrows():
        if pd.isna(row['Reopen count']):
            status = "⚠️ Invalid (excluded)"
        elif row['Reopen count'] == 0:
            status = "✓ First Contact"
        else:
            status = f"✗ Reopened ({int(row['Reopen count'])}x)"
        print(f"{row['ticket_id']}: Reopen count = {row['Reopen count']} → {status}")
    
    print("\n" + "="*60)
    
    print("Overall FCR Calculation:")
    print(f"Total Incidents: {fcr_results['total_incidents']}")
    print(f"Valid Incidents: {fcr_results['valid_incidents']}")
    print(f"Invalid/Unknown: {fcr_results['unknown_count']}")
    print(f"First Contact Resolutions: {fcr_results['fcr_count']}")
    print(f"Reopened Incidents: {fcr_results['non_fcr_count']}")
    print(f"FCR Rate: ({fcr_results['fcr_count']}/{fcr_results['valid_incidents']}) × 100 = {fcr_results['fcr_percentage']:.1f}%")
    
    return df

def reopen_distribution_analysis(df):
    """
    Analyze the distribution of reopen counts
    """
    print("\n" + "="*60)
    print("Reopen Count Distribution Analysis")
    print("="*60)
    
    # Get valid reopen counts only
    valid_reopens = df[df['Reopen count'].notna()]['Reopen count']
    
    if len(valid_reopens) > 0:
        # Distribution
        distribution = valid_reopens.value_counts().sort_index()
        
        print("Reopen Count Distribution:")
        for reopen_count, count in distribution.items():
            percentage = (count / len(valid_reopens)) * 100
            print(f"  {int(reopen_count)} reopens: {count} incidents ({percentage:.1f}%)")
        
        # Statistics for reopened incidents only
        reopened_only = df[df['Reopen count'] > 0]['Reopen count']
        if len(reopened_only) > 0:
            print(f"\nReopened Incidents Statistics:")
            print(f"  Average reopens: {reopened_only.mean():.2f}")
            print(f"  Max reopens: {int(reopened_only.max())}")
            print(f"  Total reopened: {len(reopened_only)}")
    
    return distribution

def monthly_fcr_calculation(df):
    """
    Demonstrates how FCR is calculated by month with proper validation
    """
    print("\n" + "="*60)
    print("Monthly FCR Calculation (with Validation)")
    print("="*60)
    
    # Group by month
    monthly_stats = []
    for month in df['created_month'].unique():
        month_data = df[df['created_month'] == month]
        fcr_results = calculate_fcr_with_validation(month_data)
        
        monthly_stats.append({
            'month': month,
            'total': fcr_results['total_incidents'],
            'valid': fcr_results['valid_incidents'],
            'fcr': fcr_results['fcr_count'],
            'fcr_pct': fcr_results['fcr_percentage']
        })
    
    # Display results
    print("Monthly FCR Breakdown:")
    print(f"{'Month':<10} {'Total':<8} {'Valid':<8} {'FCR':<8} {'FCR %':<8}")
    print("-" * 42)
    for stat in monthly_stats:
        print(f"{stat['month']:<10} {stat['total']:<8} {stat['valid']:<8} {stat['fcr']:<8} {stat['fcr_pct']:<8.1f}")
    
    return monthly_stats

def team_fcr_calculation(df):
    """
    Demonstrates how FCR is calculated by team with proper validation
    """
    print("\n" + "="*60)
    print("Team FCR Calculation (with Validation)")
    print("="*60)
    
    # Group by team
    team_stats = []
    for team in df['assignment_group'].unique():
        team_data = df[df['assignment_group'] == team]
        fcr_results = calculate_fcr_with_validation(team_data)
        
        team_stats.append({
            'team': team,
            'total': fcr_results['total_incidents'],
            'valid': fcr_results['valid_incidents'],
            'fcr': fcr_results['fcr_count'],
            'fcr_pct': fcr_results['fcr_percentage']
        })
    
    # Sort by FCR percentage
    team_stats.sort(key=lambda x: x['fcr_pct'], reverse=True)
    
    # Display results
    print("Team FCR Breakdown:")
    print(f"{'Team':<10} {'Total':<8} {'Valid':<8} {'FCR':<8} {'FCR %':<8}")
    print("-" * 42)
    for stat in team_stats:
        print(f"{stat['team']:<10} {stat['total']:<8} {stat['valid']:<8} {stat['fcr']:<8} {stat['fcr_pct']:<8.1f}")
    
    return team_stats

def dashboard_implementation_notes():
    """
    Shows how to implement improved FCR logic in the dashboard
    """
    print("\n" + "="*60)
    print("Dashboard Implementation Notes - Improved FCR")
    print("="*60)
    
    implementation_code = '''
# UPDATED app.py - Data Loading:
# Ensure reopen count is numeric and handle invalid values
incidents_df['Reopen count'] = pd.to_numeric(incidents_df['Reopen count'], errors='coerce')

# In api_overview() and other endpoints:
# Calculate FCR excluding invalid reopen counts
valid_incidents = filtered_df[filtered_df['Reopen count'].notna()]
fcr_rate = (valid_incidents['Reopen count'] == 0).sum() / len(valid_incidents) * 100 if len(valid_incidents) > 0 else 0

# For monthly/team aggregations:
# Update lambda to handle invalid values
'Reopen count': lambda x: (x[x.notna()] == 0).sum() / x.notna().sum() * 100 if x.notna().sum() > 0 else 0

# Alternative approach - filter first:
valid_df = df[df['Reopen count'].notna()]
monthly_data = valid_df.groupby(valid_df['Created'].dt.to_period('M')).agg({
    'Number': 'count',
    'Reopen count': lambda x: (x == 0).sum() / len(x) * 100
})

# Display reopen distribution in team performance:
reopen_stats = team_incidents[team_incidents['Reopen count'] > 0]['Reopen count']
avg_reopens = reopen_stats.mean() if len(reopen_stats) > 0 else 0
max_reopens = reopen_stats.max() if len(reopen_stats) > 0 else 0
    '''
    
    print("Key Changes for Dashboard:")
    print(implementation_code)
    
    print("\nKey Implementation Points:")
    print("1. Use pd.to_numeric() with errors='coerce' for reopen count")
    print("2. Filter out invalid reopen counts before FCR calculation")
    print("3. Update aggregation lambdas to handle NaN values")
    print("4. Add validation checks to prevent division by zero")
    print("5. Optionally display reopen distribution statistics")
    print("\nBenefits:")
    print("- More accurate FCR calculation")
    print("- Handles data quality issues gracefully")
    print("- Provides clearer metrics by excluding invalid data")
    print("- Better insights into reopen patterns")

def analyze_real_data():
    """
    Analyze FCR using the actual data with improved validation
    """
    df = load_new_incident_data()
    if df is None:
        print("❌ Cannot proceed without data")
        return
    
    print("\n" + "="*60)
    print("🔍 REAL DATA FCR ANALYSIS (With Validation)")
    print("="*60)
    
    # Calculate overall FCR with validation
    fcr_results = calculate_fcr_with_validation(df)
    
    print(f"📊 OVERALL FCR METRICS:")
    print(f"   Total Incidents: {fcr_results['total_incidents']:,}")
    print(f"   Valid Incidents: {fcr_results['valid_incidents']:,}")
    if fcr_results['unknown_count'] > 0:
        print(f"   Invalid/Unknown: {fcr_results['unknown_count']:,} ({fcr_results['unknown_count']/fcr_results['total_incidents']*100:.1f}%)")
    print(f"   First Contact Resolutions: {fcr_results['fcr_count']:,}")
    print(f"   Reopened Incidents: {fcr_results['non_fcr_count']:,}")
    print(f"   FCR Rate: {fcr_results['fcr_percentage']:.1f}%")
    
    # Reopen distribution for non-FCR incidents
    print(f"\n📊 REOPEN DISTRIBUTION (for reopened incidents):")
    reopened_df = df[df['Reopen count'] > 0]
    if len(reopened_df) > 0:
        distribution = reopened_df['Reopen count'].value_counts().sort_index().head(10)
        for reopen_count, count in distribution.items():
            print(f"   {int(reopen_count)} reopens: {count:,} incidents")
        print(f"   Average reopens: {reopened_df['Reopen count'].mean():.2f}")
        print(f"   Max reopens: {int(reopened_df['Reopen count'].max())}")
    
    # Monthly breakdown
    print(f"\n📅 MONTHLY FCR BREAKDOWN:")
    df['created_month'] = df['Created'].dt.to_period('M')
    for month in sorted(df['created_month'].unique()):
        month_data = df[df['created_month'] == month]
        month_results = calculate_fcr_with_validation(month_data)
        print(f"   {month}: {month_results['valid_incidents']:,} valid incidents, FCR: {month_results['fcr_percentage']:.1f}%")
    
    # Teams with lowest FCR (need improvement)
    print(f"\n⚠️  TEAMS WITH LOWEST FCR (Bottom 5):")
    team_fcr = []
    for team in df['Assignment group'].unique():
        team_data = df[df['Assignment group'] == team]
        team_results = calculate_fcr_with_validation(team_data)
        if team_results['valid_incidents'] >= 10:  # Only teams with significant volume
            team_fcr.append({
                'team': team,
                'fcr': team_results['fcr_percentage'],
                'valid': team_results['valid_incidents'],
                'reopened': team_results['non_fcr_count']
            })
    
    team_fcr.sort(key=lambda x: x['fcr'])
    for team_stat in team_fcr[:5]:
        print(f"   {team_stat['team']}: FCR {team_stat['fcr']:.1f}% ({team_stat['reopened']} reopened out of {team_stat['valid']})")
    
    return df

if __name__ == "__main__":
    print("🎯 FCR (First Contact Resolution) Analysis - Enhanced")
    print("📁 Using: Combined_Incidents_Report_Feb_to_June_2025.xlsx")
    
    # Run real data analysis first
    real_df = analyze_real_data()
    
    # Then run the demonstration with sample data
    print("\n" + "="*60)
    print("📚 DEMONSTRATION WITH SAMPLE DATA")
    print("="*60)
    df = calculate_fcr_example()
    reopen_distribution_analysis(df)
    monthly_fcr_calculation(df)
    team_fcr_calculation(df)
    dashboard_implementation_notes()
    
    print("\n" + "="*60)
    print("✅ FCR Analysis Complete!")
    print("Enhanced logic handles invalid data and provides better insights.")
    print("="*60) 