from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import sys
from MTTR import calculate_business_minutes  # Import business hours calculation


# Timezone utilities
def ensure_tz_aware(dt, default_tz='UTC'):
    '''Ensure a datetime object has timezone information'''
    if dt is None:
        return None
    
    if isinstance(dt, pd.Timestamp):
        if dt.tzinfo is None:
            return dt.tz_localize(default_tz)
        return dt
    
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            from pytz import timezone
            return timezone(default_tz).localize(dt)
        return dt
    
    return dt

def now_with_tz(tz=None):
    '''Get current time with timezone'''
    now = datetime.now()
    if tz is None:
        return now.replace(tzinfo=pd.Timestamp.now().tzinfo)
    else:
        from pytz import timezone
        return timezone(tz).localize(now)

app = Flask(__name__)
CORS(app)

# Custom JSON encoder to handle pandas and numpy types
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif pd.isna(obj):
            return None
        return super().default(obj)

# Override Flask's default JSON encoder
app.json_encoder = CustomJSONEncoder

# Global error handler for API endpoints
@app.errorhandler(Exception)
def handle_exception(e):
    # Log the error
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    
    # Return JSON response for API endpoints
    if request.path.startswith('/api/'):
        return jsonify({
            'error': str(e),
            'status': 'error',
            'message': 'An error occurred processing your request'
        }), 500
    # Return error page for web pages
    return render_template('error.html', error=str(e)), 500

# Memory management - function to clean up large dataframes
def cleanup_memory():
    """Release memory from large temporary dataframes"""
    import gc
    gc.collect()
    print("🧹 Memory cleanup performed")

# Define fiscal year quarters and date ranges once for consistency
FY26_QUARTERS = {
    'Q1': {'months': [2, 3, 4], 'name': 'Q1 FY26 (Feb-Apr 2025)'},
    'Q2': {'months': [5, 6], 'name': 'Q2 FY26 (May-Jun 2025)'}
}

def standardize_date(date_str):
    """Detect and standardize various date formats to ISO format
    
    Handles formats like:
    - MM/DD/YYYY
    - DD/MM/YYYY
    - YYYY/MM/DD
    - MM-DD-YYYY
    - DD-MM-YYYY
    - YYYY-MM-DD
    - Month DD, YYYY
    
    Returns a pandas Timestamp object with UTC timezone
    """
    if pd.isna(date_str) or not date_str:
        return None
        
    # If already a datetime object, just ensure timezone
    if isinstance(date_str, (pd.Timestamp, datetime)):
        if date_str.tzinfo is None:
            return pd.Timestamp(date_str, tz='UTC')
        return date_str
    
    date_str = str(date_str).strip()
    
    # Try multiple date formats
    date_formats = [
        # ISO format
        '%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', 
        # US format
        '%m/%d/%Y', '%m/%d/%Y %H:%M:%S', '%m-%d-%Y', '%m-%d-%Y %H:%M:%S',
        # European format
        '%d/%m/%Y', '%d/%m/%Y %H:%M:%S', '%d-%m-%Y', '%d-%m-%Y %H:%M:%S',
        # Other common formats
        '%b %d, %Y', '%B %d, %Y', '%d %b %Y', '%d %B %Y'
    ]
    
    for fmt in date_formats:
        try:
            dt = pd.to_datetime(date_str, format=fmt)
            return pd.Timestamp(dt, tz='UTC')
        except (ValueError, TypeError):
            continue
    
    # If all specific formats fail, try pandas' flexible parser
    try:
        dt = pd.to_datetime(date_str)
        return pd.Timestamp(dt, tz='UTC')
    except (ValueError, TypeError):
        print(f"⚠️ Could not parse date: {date_str}")
        return None

def get_date_range_for_quarter(quarter):
    """Get start and end dates for a specific quarter"""
    if ensure_tz_aware(quarter) == ensure_tz_aware('Q1'):
        return pd.Timestamp('2025-02-01', tz='UTC'), pd.Timestamp('2025-04-30 23:59:59', tz='UTC')
    elif ensure_tz_aware(quarter) == ensure_tz_aware('Q2'):
        return pd.Timestamp('2025-05-01', tz='UTC'), pd.Timestamp('2025-06-30 23:59:59', tz='UTC')
    else:
        return pd.Timestamp('2025-02-01', tz='UTC'), pd.Timestamp('2025-06-30 23:59:59', tz='UTC')

def parse_month_parameter(month):
    """Parse month parameter for drill-downs and return start and end dates
    
    Handles various month formats:
    - YYYY-MM (e.g., 2025-03)
    - Month name with year (e.g., March 2025, Mar 2025)
    - Any format supported by standardize_date
    
    Returns:
        tuple: (start_date, end_date) as UTC Timestamps, or (None, None) if parsing fails
    """
    if not month or month == 'all':
        return None, None
        
    try:
        # Try to handle various month formats
        # First check if it's in YYYY-MM format
        if '-' in month and len(month.split('-')) == 2:
            year, month_num = month.split('-')
            try:
                # Validate year and month
                year = int(year)
                month_num = int(month_num)
                
                # Create proper date range for the entire month
                start_date = pd.Timestamp(f"{year}-{month_num:02d}-01", tz='UTC')
                
                # Calculate end of month correctly
                if ensure_tz_aware(month_num) == ensure_tz_aware(12):
                    end_date = pd.Timestamp(f"{year+1}-01-01", tz='UTC') - pd.Timedelta(seconds=1)
                else:
                    end_date = pd.Timestamp(f"{year}-{month_num+1:02d}-01", tz='UTC') - pd.Timedelta(seconds=1)
                    
                return start_date, end_date
            except (ValueError, TypeError):
                pass
        
        # Try adding a day to make it a full date
        parsed_date = standardize_date(month + "-01")
        if parsed_date is not None:
            # Get year and month from parsed date
            year = parsed_date.year
            month_num = parsed_date.month
            
            # Create proper date range
            start_date = pd.Timestamp(f"{year}-{month_num:02d}-01", tz='UTC')
            if ensure_tz_aware(month_num) == ensure_tz_aware(12):
                end_date = pd.Timestamp(f"{year+1}-01-01", tz='UTC') - pd.Timedelta(seconds=1)
            else:
                end_date = pd.Timestamp(f"{year}-{month_num+1:02d}-01", tz='UTC') - pd.Timedelta(seconds=1)
                
            return start_date, end_date
        
        # Try to parse as a date string like "January 2025" or "Jan 2025"
        parsed_date = standardize_date(f"01 {month}")
        if parsed_date is None:
            parsed_date = standardize_date(month + " 01")
        
        if parsed_date is not None:
            year = parsed_date.year
            month_num = parsed_date.month
            
            # Create proper date range
            start_date = pd.Timestamp(f"{year}-{month_num:02d}-01", tz='UTC')
            if ensure_tz_aware(month_num) == ensure_tz_aware(12):
                end_date = pd.Timestamp(f"{year+1}-01-01", tz='UTC') - pd.Timedelta(seconds=1)
            else:
                end_date = pd.Timestamp(f"{year}-{month_num+1:02d}-01", tz='UTC') - pd.Timedelta(seconds=1)
                
            return start_date, end_date
            
    except Exception as e:
        print(f"Error parsing month parameter: {month}, error: {e}")
        
    return None, None


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

# Global variables to store data
incidents_df = None
consultations_df = None
regions_df = None

def load_data():
    """Load and preprocess the incidents data and consultation data"""
    global incidents_df, consultations_df, regions_df
    try:
        # Determine the base path for data files
        if getattr(sys, 'frozen', False):
            # If bundled by PyInstaller
            base_path = sys._MEIPASS
        else:
            # If running normally
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Construct full paths to data files
        incidents_file = os.path.join(base_path, 'Combined_Incidents_Report_Feb_to_June_2025.xlsx')
        
        # Check if incidents file exists
        if not os.path.exists(incidents_file):
            print(f"❌ Error: Incidents data file not found: {incidents_file}")
            print("Searching for alternative data files...")
            # Try alternative file names
            alternative_files = ['FY26-6Months.xlsx', 'incidents.xlsx', 'Combined_Incidents_Report.xlsx']
            for alt_file in alternative_files:
                alt_path = os.path.join(base_path, alt_file)
                if os.path.exists(alt_path):
                    print(f"✅ Found alternative data file: {alt_file}")
                    incidents_file = alt_path
                    break
            else:
                print("❌ No suitable data files found. Dashboard may not function correctly.")
                return False
        
        # Load incidents data file
        print(f"📊 Loading incidents data from: {os.path.basename(incidents_file)}")
        incidents_df = pd.read_excel(incidents_file)
        
        # Convert date columns with robust format detection and consistent timezone handling
        print("Standardizing date formats for incidents data...")
        
        # Apply standardize_date to handle various date formats
        incidents_df['Created'] = incidents_df['Created'].apply(standardize_date)
        incidents_df['Opened'] = incidents_df['Opened'].apply(standardize_date)
        incidents_df['Resolved'] = incidents_df['Resolved'].apply(standardize_date)
        incidents_df['Closed'] = incidents_df['Closed'].apply(standardize_date)
        
        # Report any date parsing issues
        date_columns = ['Created', 'Opened', 'Resolved', 'Closed']
        for col in date_columns:
            null_count = incidents_df[col].isna().sum()
            if ensure_tz_aware(null_count) > ensure_tz_aware(0):
                print(f"⚠️ Found {null_count} unparseable dates in {col} column")
        
        # Add local timezone versions for display purposes
        incidents_df['Created_Local'] = incidents_df['Created'].dt.tz_convert('America/Los_Angeles')
        incidents_df['Resolved_Local'] = incidents_df['Resolved'].dt.tz_convert('America/Los_Angeles')
        
        # Add weekday flag (Monday=0, Sunday=6) - exclude Saturday (5) and Sunday (6)
        incidents_df['created_weekday'] = incidents_df['Created'].dt.dayofweek
        incidents_df['is_weekday_created'] = incidents_df['created_weekday'] < 5  # Monday-Friday only
        
        # Calculate MTTR using business hours (excluding weekends)
        # Apply business hours calculation to all resolved incidents
        resolved_mask = incidents_df['Resolved'].notna() & incidents_df['Created'].notna()
        
        # Calculate business hours MTTR
        incidents_df['MTTR_business_minutes'] = incidents_df.apply(
            lambda row: calculate_business_minutes(row['Created'], row['Resolved']) 
            if pd.notna(row['Created']) and pd.notna(row['Resolved']) else np.nan,
            axis=1
        )
        
        # Keep the total elapsed time for comparison
        incidents_df['MTTR_total_minutes'] = incidents_df.apply(
            lambda row: (row['Resolved'] - row['Created']).total_seconds() / 60 
            if pd.notna(row['Created']) and pd.notna(row['Resolved']) else np.nan,
            axis=1
        )
        
        # For backwards compatibility, set MTTR_calculated to business hours value
        incidents_df['MTTR_calculated'] = incidents_df['MTTR_business_minutes']
        
        # Validate existing 'Resolve time' column
        incidents_df['Resolve time'] = pd.to_numeric(incidents_df['Resolve time'], errors='coerce')
        
        # Report data quality - compare with original resolve time if available
        resolved_with_time = incidents_df[resolved_mask & incidents_df['Resolve time'].notna()]
        if len(resolved_with_time) > 0:
            avg_diff = abs(resolved_with_time['Resolve time'] - resolved_with_time['MTTR_total_minutes']).mean()
            if ensure_tz_aware(avg_diff) > ensure_tz_aware(10):
                print(f"⚠️  Data quality: Original 'Resolve time' differs from calculated by avg {avg_diff:.1f} minutes")
        
        # Calculate SLA compliance based on MTTR calculations
        # Define consistent SLA thresholds
        SLA_THRESHOLD_MINUTES = 240  # Baseline SLA: 4 hours (240 minutes)
        SLA_GOAL_MINUTES = 192       # Goal SLA: 3 hours 12 minutes (192 minutes)
        
        # Use business hours MTTR for all SLA calculations
        incidents_df['sla_met_baseline'] = incidents_df['MTTR_business_minutes'] <= SLA_THRESHOLD_MINUTES
        incidents_df['sla_met_goal'] = incidents_df['MTTR_business_minutes'] <= SLA_GOAL_MINUTES
        
        # For backwards compatibility
        incidents_df['sla_met_mttr'] = incidents_df['sla_met_baseline']
        
        # Use the existing 'Made SLA' column as a reference but prefer calculated values
        incidents_df['sla_met_native'] = incidents_df['Made SLA'].fillna(False)
        
        # SLA Breach calculation: incidents exceeding promised timelines
        incidents_df['sla_promised_minutes'] = SLA_THRESHOLD_MINUTES  # Use consistent variable
        incidents_df['sla_breached'] = incidents_df['MTTR_business_minutes'] > incidents_df['sla_promised_minutes']
        incidents_df['sla_variance_minutes'] = incidents_df['MTTR_business_minutes'] - incidents_df['sla_promised_minutes']
        
        # Convert numeric columns with better error handling
        try:
            incidents_df['Resolve time'] = pd.to_numeric(incidents_df['Resolve time'], errors='coerce')
            # Fill NaN values with a reasonable default to prevent calculation errors
            incidents_df['Resolve time'].fillna(incidents_df['MTTR_business_minutes'], inplace=True)
            
            incidents_df['Reopen count'] = pd.to_numeric(incidents_df['Reopen count'], errors='coerce')
            # Fill NaN values with 0 for reopen count
            incidents_df['Reopen count'].fillna(0, inplace=True)
            
            # Report data quality issues
            invalid_resolve_time = incidents_df['Resolve time'].isna().sum()
            invalid_reopen_count = incidents_df['Reopen count'].isna().sum()
            
            if ensure_tz_aware(invalid_resolve_time) > ensure_tz_aware(0):
                print(f"⚠️  Fixed {invalid_resolve_time} invalid resolve times with calculated MTTR values")
                
            if ensure_tz_aware(invalid_reopen_count) > ensure_tz_aware(0):
                print(f"⚠️  Fixed {invalid_reopen_count} invalid reopen counts (set to 0)")
        except Exception as e:
            print(f"⚠️  Error converting numeric columns: {e}")
            print("Continuing with partial data conversion")
        
        # Data validation
        resolved_incidents = incidents_df['Resolved'].notna().sum()
        weekday_incidents = incidents_df['is_weekday_created'].sum()
        weekend_incidents = len(incidents_df) - weekday_incidents
        sla_met_native = incidents_df['sla_met_native'].sum()
        sla_met_mttr = incidents_df['sla_met_mttr'].sum()
        sla_met_goal = incidents_df['sla_met_goal'].sum()
        sla_compliance_native = (sla_met_native / len(incidents_df)) * 100
        sla_compliance_mttr = (sla_met_mttr / len(incidents_df)) * 100
        sla_compliance_goal = (sla_met_goal / len(incidents_df)) * 100
        sla_breaches = incidents_df['sla_breached'].sum()
        sla_breach_rate = (sla_breaches / len(incidents_df)) * 100
        print(f"Data loaded successfully: {len(incidents_df)} incidents")
        print(f"Date range: {incidents_df['Created'].min()} to {incidents_df['Created'].max()}")
        print(f"Resolved incidents: {resolved_incidents}/{len(incidents_df)}")
        print(f"Valid resolution times: {incidents_df['Resolve time'].notna().sum()}/{len(incidents_df)}")
        print(f"Weekday incidents: {weekday_incidents}, Weekend incidents: {weekend_incidents} (excluded from MTTR)")
        print(f"SLA compliance (native): {sla_met_native}/{len(incidents_df)} = {sla_compliance_native:.1f}%")
        print(f"SLA compliance (MTTR-based): {sla_met_mttr}/{len(incidents_df)} = {sla_compliance_mttr:.1f}%")
        print(f"SLA goal compliance (192-min goal): {sla_met_goal}/{len(incidents_df)} = {sla_compliance_goal:.1f}%")
        print(f"SLA breaches (240-min promise): {sla_breaches}/{len(incidents_df)} = {sla_breach_rate:.1f}%")
        print(f"Teams: {incidents_df['Assignment group'].nunique()} unique assignment groups")
        
        # MTTR analysis - now using business hours
        resolved_incidents_df = incidents_df[incidents_df['Resolved'].notna()]
        avg_mttr_business = resolved_incidents_df['MTTR_business_minutes'].mean()
        avg_mttr_total = resolved_incidents_df['MTTR_total_minutes'].mean()
        print(f"MTTR Analysis:")
        print(f"  Average MTTR (business hours): {avg_mttr_business/60:.1f} hours")
        print(f"  Average MTTR (total elapsed): {avg_mttr_total/60:.1f} hours")
        print(f"  Weekend time excluded: {(avg_mttr_total - avg_mttr_business)/60:.1f} hours")
        
        # Load regions mapping data
        try:
            regions_file = os.path.join(base_path, 'Regions-Groups.xlsx')
            regions_df = pd.read_excel(regions_file)
            
            # Create region mapping and add to incidents_df
            region_mapping = dict(zip(regions_df['Assignment Groups'], regions_df['Region']))
            
            # Add manual mappings for the two missing groups
            region_mapping['ADE - Enterprise Tech Spot 2 - IDC PTP1 '] = 'IDC'  # Note the trailing space
            region_mapping['SD - Puerto Rico - Regional Office Tech Support'] = 'Puerto Rico'
            
            incidents_df['Region'] = incidents_df['Assignment group'].map(region_mapping)
            
            # Check if there are any unmapped groups (should be 0 now)
            unmapped_count = incidents_df['Region'].isna().sum()
            if ensure_tz_aware(unmapped_count) > ensure_tz_aware(0):
                print(f"Warning: {unmapped_count} incidents still unmapped to regions")
                # Fill any remaining unmapped groups with 'Unknown' as fallback
                incidents_df['Region'] = incidents_df['Region'].fillna('Unknown')
            else:
                print("✅ All assignment groups successfully mapped to regions")
            
            # Report region mapping results
            mapped_groups = incidents_df['Assignment group'][incidents_df['Region'] != 'Unknown'].nunique()
            total_groups = incidents_df['Assignment group'].nunique()
            region_counts = incidents_df['Region'].value_counts()
            
            print(f"Region mapping loaded: {mapped_groups}/{total_groups} assignment groups mapped")
            print(f"Region distribution:")
            for region, count in region_counts.items():
                percentage = (count / len(incidents_df)) * 100
                print(f"  {region}: {count} incidents ({percentage:.1f}%)")
                
        except Exception as e:
            print(f"Warning: Could not load regions data: {e}")
            regions_df = None
            incidents_df['Region'] = 'Unknown'
        
        # Load Pre-TSQ consultation data from new Excel file
        try:
            consultations_file = os.path.join(base_path, 'Pre-TSQ Data-FebTOJune2025.xlsx')
            consultations_df = pd.read_excel(consultations_file, sheet_name='Pre-TSQ Data (6)')
            
            # Convert date columns with robust format detection and consistent timezone handling
            print("Standardizing date formats for consultations data...")
            
            # Apply standardize_date to handle various date formats
            consultations_df['Created'] = consultations_df['Created'].apply(standardize_date)
            consultations_df['Modified'] = consultations_df['Modified'].apply(standardize_date)
            
            # Report any date parsing issues
            date_columns = ['Created', 'Modified']
            for col in date_columns:
                null_count = consultations_df[col].isna().sum()
                if ensure_tz_aware(null_count) > ensure_tz_aware(0):
                    print(f"⚠️ Found {null_count} unparseable dates in {col} column")
            
            # Add local timezone versions for display purposes
            consultations_df['Created_Local'] = consultations_df['Created'].dt.tz_convert('America/Los_Angeles')
            consultations_df['Modified_Local'] = consultations_df['Modified'].dt.tz_convert('America/Los_Angeles')
            
            # Filter to match incident data timeframe (February-June only, exclude January and July)
            consultations_df = consultations_df[
                (consultations_df['Created'].dt.month >= 2) & 
                (consultations_df['Created'].dt.month <= 6)
            ]
            
            # Filter out "Virtual Tech Spot Reservation (TECH USE ONLY)"
            consultations_df = consultations_df[consultations_df['Location'] != "Virtual Tech Spot Reservation (TECH USE ONLY)"]
            
            # Clean up data
            consultations_df['Consult Complete'] = consultations_df['Consult Complete'].fillna('No')
            consultations_df['Location'] = consultations_df['Location'].fillna('Unknown')
            consultations_df['Technician Name'] = consultations_df['Technician Name'].fillna('Unknown')
            
            # Add region mapping based on location
            def map_location_to_region(location):
                # Central Region
                if any(term in str(location) for term in [
                    "Sam's Home Office",
                    "Home Office",
                    "J Street",
                    "David Glass Technology Center",
                    "I Street"
                ]):
                    return "Central Region"
                # IDC
                elif any(term in str(location) for term in [
                    "IDC - Building 11",
                    "IDC - Building 10",
                    "IDC - PW II",
                    "IDC - RMZ"
                ]):
                    return "IDC"
                # East Region
                elif any(term in str(location) for term in [
                    "Charlotte",
                    "Hoboken",
                    "Reston",
                    "Aviation",
                    "Hula",
                    "MLK",
                    "Ol Roy",
                    "Purpose",
                    "Transportation"
                ]):
                    return "East Region"
                # West Region
                elif any(term in str(location) for term in [
                    "Los Angeles",
                    "Bellevue",
                    "Sunnyvale",
                    "San Bruno"
                ]):
                    return "West Region"
                # Puerto Rico
                elif "Puerto Rico" in str(location):
                    return "Puerto Rico"
                else:
                    return "Other"
            
            # Apply the mapping to create a new Region column
            consultations_df['Region'] = consultations_df['Location'].apply(map_location_to_region)
            
            # Print region distribution for consultations
            region_counts = consultations_df['Region'].value_counts()
            print(f"Consultation region distribution:")
            for region, count in region_counts.items():
                percentage = (count / len(consultations_df)) * 100
                print(f"  {region}: {count} consultations ({percentage:.1f}%)")
            
            # Calculate consultation metrics
            total_consultations = len(consultations_df)
            completed_consultations = (consultations_df['Consult Complete'] == 'Yes').sum()
            completion_rate = (completed_consultations / total_consultations) * 100 if total_consultations > 0 else 0
            
            print(f"Consultation data loaded: {total_consultations} consultations")
            print(f"Date range: {consultations_df['Created'].min()} to {consultations_df['Created'].max()}")
            print(f"Completion rate: {completed_consultations}/{total_consultations} = {completion_rate:.1f}%")
            print(f"Locations: {consultations_df['Location'].nunique()} unique locations")
            print(f"Technicians: {consultations_df['Technician Name'].nunique()} unique technicians")
            
        except Exception as e:
            print(f"Warning: Could not load consultation data: {e}")
            consultations_df = None
        
        return True
    except Exception as e:
        print(f"Error loading data: {e}")
        return False

def get_monthly_trends():
    """Calculate monthly trends for incidents"""
    if incidents_df is None:
        return []
    
    # Group by month and ensure we have all months in the data range
    # MTTR now uses business hours calculation, no need for weekday filtering
    monthly_data = incidents_df.groupby(incidents_df['Created'].dt.to_period('M')).agg({
        'Number': 'count',
        'MTTR_calculated': 'mean',  # Business hours MTTR
        'Reopen count': lambda x: (x[x.notna()] == 0).sum() / x.notna().sum() * 100 if x.notna().sum() > 0 else 0,  # FCR with validation
        'sla_met_mttr': lambda x: (incidents_df.loc[x.index, 'sla_met_mttr']).sum() / len(x) * 100,  # SLA compliance based on MTTR
        'sla_met_goal': lambda x: (incidents_df.loc[x.index, 'sla_met_goal']).sum() / len(x) * 100,  # SLA goal compliance
        'sla_breached': lambda x: (incidents_df.loc[x.index, 'sla_breached']).sum()  # SLA breach count per month
    }).round(2)
    
    # Sort by month to ensure chronological order
    monthly_data = monthly_data.sort_index()
    
    trends = []
    for period, row in monthly_data.iterrows():
        trends.append({
            'month': str(period),
            'incidents': int(row['Number']),
            'avg_resolution_time': float(row['MTTR_calculated']) if not pd.isna(row['MTTR_calculated']) else 0,
            'fcr_rate': float(row['Reopen count'])
        })
    
    return trends

def get_monthly_trends_filtered(df):
    """Calculate monthly trends for filtered incidents data"""
    if df is None or len(df) == 0:
        return []
    
    # Group by month and ensure we have all months in the data range
    # MTTR now uses business hours calculation, no need for weekday filtering
    monthly_data = df.groupby(df['Created'].dt.to_period('M')).agg({
        'Number': 'count',
        'MTTR_calculated': 'mean',  # Business hours MTTR
        'Reopen count': lambda x: (x[x.notna()] == 0).sum() / x.notna().sum() * 100 if x.notna().sum() > 0 else 0,  # FCR with validation
        'sla_met_mttr': lambda x: (df.loc[x.index, 'sla_met_mttr']).sum() / len(x) * 100,  # SLA compliance based on MTTR
        'sla_met_goal': lambda x: (df.loc[x.index, 'sla_met_goal']).sum() / len(x) * 100,  # SLA goal compliance
        'sla_breached': lambda x: (df.loc[x.index, 'sla_breached']).sum()  # SLA breach count per month
    }).round(2)
    
    # Sort by month to ensure chronological order
    monthly_data = monthly_data.sort_index()
    
    trends = []
    for period, row in monthly_data.iterrows():
        trends.append({
            'month': str(period),
            'incidents': int(row['Number']),
            'avg_resolution_time': float(row['MTTR_calculated']) if not pd.isna(row['MTTR_calculated']) else 0,
            'fcr_rate': float(row['Reopen count']),
            'sla_compliance_mttr': float(row['sla_met_mttr']),
            'sla_goal_compliance': float(row['sla_met_goal']),
            'sla_breaches': int(row['sla_breached'])
        })
    
    return trends

def apply_filters(df, quarter=None, month=None, region=None, assignment_group=None):
    """Apply quarter, month, region, and assignment group filters to a dataframe"""
    filtered_df = df.copy()
    
    # Apply month filter (takes precedence over quarter)
    if month and month != 'all':
        try:
            # Try to handle various month formats
            # First check if it's in YYYY-MM format
            if '-' in month and len(month.split('-')) == 2:
                year, month_num = month.split('-')
                try:
                    # Validate year and month
                    year = int(year)
                    month_num = int(month_num)
                    
                    # Create proper date range for the entire month
                    start_date = pd.Timestamp(f"{year}-{month_num:02d}-01", tz='UTC')
                    
                    # Calculate end of month correctly
                    if ensure_tz_aware(month_num) == ensure_tz_aware(12):
                        end_date = pd.Timestamp(f"{year+1}-01-01", tz='UTC') - pd.Timedelta(seconds=1)
                    else:
                        end_date = pd.Timestamp(f"{year}-{month_num+1:02d}-01", tz='UTC') - pd.Timedelta(seconds=1)
                except (ValueError, TypeError):
                    # If parsing fails, try standardize_date
                    parsed_date = standardize_date(month + "-01")
                    if parsed_date is not None:
                        # Get year and month from parsed date
                        year = parsed_date.year
                        month_num = parsed_date.month
                        
                        # Create proper date range
                        start_date = pd.Timestamp(f"{year}-{month_num:02d}-01", tz='UTC')
                        if ensure_tz_aware(month_num) == ensure_tz_aware(12):
                            end_date = pd.Timestamp(f"{year+1}-01-01", tz='UTC') - pd.Timedelta(seconds=1)
                        else:
                            end_date = pd.Timestamp(f"{year}-{month_num+1:02d}-01", tz='UTC') - pd.Timedelta(seconds=1)
                    else:
                        raise ValueError(f"Could not parse month: {month}")
            else:
                # Try to parse as a date string like "January 2025" or "Jan 2025"
                parsed_date = standardize_date(f"01 {month}")
                if parsed_date is None:
                    parsed_date = standardize_date(month + " 01")
                
                if parsed_date is not None:
                    year = parsed_date.year
                    month_num = parsed_date.month
                    
                    # Create proper date range
                    start_date = pd.Timestamp(f"{year}-{month_num:02d}-01", tz='UTC')
                    if ensure_tz_aware(month_num) == ensure_tz_aware(12):
                        end_date = pd.Timestamp(f"{year+1}-01-01", tz='UTC') - pd.Timedelta(seconds=1)
                    else:
                        end_date = pd.Timestamp(f"{year}-{month_num+1:02d}-01", tz='UTC') - pd.Timedelta(seconds=1)
                else:
                    print(f"Could not parse month format: {month}")
                    return filtered_df
            
            # Apply the date range filter
            filtered_df = filtered_df[
                (filtered_df['Created'] >= start_date) & 
                (filtered_df['Created'] <= end_date)
            ]
        except Exception as e:
            # Handle any errors in month parsing
            print(f"Error processing month filter: {month}, error: {e}")
            pass
    elif quarter and quarter != 'all':
        # Get date range for quarter
        start_date, end_date = get_date_range_for_quarter(quarter)
        filtered_df = filtered_df[
            (filtered_df['Created'] >= start_date) & 
            (filtered_df['Created'] <= end_date)
        ]
    
    # Apply region filter
    if region and region != 'all':
        filtered_df = filtered_df[filtered_df['Region'] == region]
    
    # Apply assignment group filter
    if assignment_group and assignment_group != 'all':
        filtered_df = filtered_df[filtered_df['Assignment group'] == assignment_group]
    
    return filtered_df

@app.route('/')
def dashboard():
    """Serve the main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/regions')
def api_regions():
    """Get available regions for filtering"""
    if incidents_df is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    regions = incidents_df['Region'].unique().tolist()
    # Sort regions - put major regions first
    region_order = ['US', 'IDC', 'Puerto Rico']
    sorted_regions = [r for r in region_order if r in regions] + [r for r in regions if r not in region_order]
    
    region_stats = []
    for region in sorted_regions:
        count = (incidents_df['Region'] == region).sum()
        percentage = (count / len(incidents_df)) * 100
        region_stats.append({
            'region': region,
            'incidents': int(count),
            'percentage': round(percentage, 1)
        })
    
    return jsonify({
        'regions': sorted_regions,
        'region_stats': region_stats
    })

@app.route('/api/assignment_groups')
def api_assignment_groups():
    """Get available assignment groups for filtering"""
    if incidents_df is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    # Get unique assignment groups
    assignment_groups = incidents_df['Assignment group'].unique().tolist()
    
    # Clean and sort assignment groups
    group_stats = []
    for group in sorted(assignment_groups):
        count = (incidents_df['Assignment group'] == group).sum()
        percentage = (count / len(incidents_df)) * 100
        
        # Clean the group name for display
        clean_name = group
        clean_name = clean_name.replace('AEDT - Enterprise Tech Spot - ', '')
        clean_name = clean_name.replace('ADE - Enterprise Tech Spot - ', '')
        clean_name = clean_name.replace('ADE - Enterprise Tech Spot 2 - ', '')
        clean_name = clean_name.replace('SD - ', '')
        
        group_stats.append({
            'group': group,
            'display_name': clean_name,
            'incidents': int(count),
            'percentage': round(percentage, 1)
        })
    
    # Sort by incident count (descending)
    group_stats.sort(key=lambda x: x['incidents'], reverse=True)
    
    return jsonify({
        'assignment_groups': [g['group'] for g in group_stats],
        'group_stats': group_stats
    })

@app.route('/api/overview')
def api_overview():
    """Get overview metrics"""
    if incidents_df is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    quarter = request.args.get('quarter', 'all')  # Default to all data
    month = request.args.get('month', 'all')  # Default to all months
    region = request.args.get('region', 'all')   # Default to all regions
    assignment_group = request.args.get('assignment_group', 'all')   # Default to all groups
    
    # Apply filters
    filtered_df = apply_filters(incidents_df, quarter, month, region, assignment_group)
    
    # Calculate key metrics
    total_incidents = len(filtered_df)
    
    # FCR Rate (First Contact Resolution): (Number of Tickets Resolved on First Contact / Total Valid Tickets) x 100
    # Where "First Contact" means reopen_count = 0, excluding invalid reopen counts
    valid_fcr_df = filtered_df[filtered_df['Reopen count'].notna()]
    fcr_rate = (valid_fcr_df['Reopen count'] == 0).sum() / len(valid_fcr_df) * 100 if len(valid_fcr_df) > 0 else 0
    
    # Resolution time stats - use business hours MTTR (no need to filter weekdays)
    avg_resolution_time = filtered_df['MTTR_calculated'].mean()
    
    # SLA compliance (native from Excel data - use this as primary SLA metric)
    sla_compliance = (filtered_df['sla_met_native'] == True).sum() / total_incidents * 100 if total_incidents > 0 else 0
    
    # SLA compliance based on MTTR (240 minutes = 4 hours baseline threshold)
    sla_compliance_mttr = (filtered_df['sla_met_mttr'] == True).sum() / total_incidents * 100 if total_incidents > 0 else 0
    
    # SLA goal compliance (192 minutes = 3 hours 12 minutes goal threshold)
    sla_goal_compliance = (filtered_df['sla_met_goal'] == True).sum() / total_incidents * 100 if total_incidents > 0 else 0
    
    # SLA breach metrics (240 minutes = 4 hours threshold)
    sla_breaches = (filtered_df['sla_breached'] == True).sum()
    sla_breach_rate = (sla_breaches / total_incidents) * 100 if total_incidents > 0 else 0
    
    # Current month vs previous month comparison (within the filtered data)
    if len(filtered_df) > 0:
        current_month = filtered_df['Created'].max().to_period('M')
        current_month_incidents = filtered_df[filtered_df['Created'].dt.to_period('M') == current_month]
    else:
        current_month_incidents = pd.DataFrame()
    
    if len(current_month_incidents) > 0:
        prev_month = current_month - 1
        prev_month_incidents = filtered_df[filtered_df['Created'].dt.to_period('M') == prev_month]
        
        if len(prev_month_incidents) > 0:
            incident_change = ((len(current_month_incidents) - len(prev_month_incidents)) / len(prev_month_incidents)) * 100
            
            # FCR comparison (excluding invalid reopen counts)
            current_valid = current_month_incidents[current_month_incidents['Reopen count'].notna()]
            prev_valid = prev_month_incidents[prev_month_incidents['Reopen count'].notna()]
            current_fcr = (current_valid['Reopen count'] == 0).sum() / len(current_valid) * 100 if len(current_valid) > 0 else 0
            prev_fcr = (prev_valid['Reopen count'] == 0).sum() / len(prev_valid) * 100 if len(prev_valid) > 0 else 0
            fcr_change = current_fcr - prev_fcr
            
            # MTTR comparison (business hours calculation)
            current_mttr = current_month_incidents['MTTR_calculated'].mean()
            prev_mttr = prev_month_incidents['MTTR_calculated'].mean()
            mttr_change = ((current_mttr - prev_mttr) / prev_mttr) * 100 if prev_mttr > 0 and not pd.isna(prev_mttr) else 0
        else:
            incident_change = 0
            fcr_change = 0
            mttr_change = 0
    else:
        incident_change = 0
        fcr_change = 0
        mttr_change = 0
    
    return jsonify({
        'total_incidents': total_incidents,
        'fcr_rate': round(fcr_rate, 1),
        'avg_resolution_time': round(avg_resolution_time / 60, 1) if not pd.isna(avg_resolution_time) else 0,  # Convert to hours
        'sla_compliance': round(sla_compliance, 1),
        'sla_compliance_mttr': round(sla_compliance_mttr, 1),
        'sla_goal_compliance': round(sla_goal_compliance, 1),
        'sla_breaches': int(sla_breaches),  # Convert to regular Python int
        'sla_breach_rate': round(sla_breach_rate, 1),
        'incident_change': round(incident_change, 1),
        'fcr_change': round(fcr_change, 1),
        'mttr_change': round(mttr_change, 1),
        'technicians': filtered_df['Resolved by'].nunique(),  # Real count from "Resolved by" field
        'locations': filtered_df['Assignment group'].nunique(),  # Real count from unique assignment groups
        'customers': total_incidents,  # Total incidents as customer interactions
        'quarter': quarter,
        'region': region
    })

@app.route('/api/trends')
def api_trends():
    """Get trends data for charts"""
    if incidents_df is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    quarter = request.args.get('quarter', 'all')  # Default to all data
    month = request.args.get('month', 'all')  # Default to all months
    region = request.args.get('region', 'all')   # Default to all regions
    assignment_group = request.args.get('assignment_group', 'all')   # Default to all groups
    
    # Apply filters
    filtered_df = apply_filters(incidents_df, quarter, month, region, assignment_group)
    
    trends = get_monthly_trends_filtered(filtered_df)
    
    # Calculate deltas for the trends
    incident_data = []
    fcr_data = []
    mttr_data = []
    sla_data = []
    breach_data = []
    
    for trend in trends:
        incident_data.append({
            'month': trend['month'],
            'value': trend['incidents']
        })
        
        fcr_data.append({
            'month': trend['month'],
            'value': trend['fcr_rate']
        })
        
        mttr_data.append({
            'month': trend['month'],
            'value': round(trend['avg_resolution_time'] / 60, 1)  # Convert to hours
        })
        
        sla_data.append({
            'month': trend['month'],
            'value': trend['sla_compliance_mttr'],
            'goal_value': trend['sla_goal_compliance']
        })
        
        breach_data.append({
            'month': trend['month'],
            'value': trend['sla_breaches']
        })
    
    # Get candlestick data for SLA chart
    # Sample recent resolved incidents for visualization
    resolved_df = filtered_df[filtered_df['Resolved'].notna()].sort_values('Created', ascending=True)
    
    # Limit to manageable number for visualization (e.g., last 200 incidents)
    sample_size = min(200, len(resolved_df))
    if ensure_tz_aware(sample_size) > ensure_tz_aware(0):
        # Take evenly spaced samples if we have too many
        if len(resolved_df) > sample_size:
            indices = np.linspace(0, len(resolved_df) - 1, sample_size, dtype=int)
            sampled_df = resolved_df.iloc[indices]
        else:
            sampled_df = resolved_df
        
        sla_candlestick_data = []
        for _, incident in sampled_df.iterrows():
            sla_candlestick_data.append({
                'mttr_minutes': float(incident['MTTR_calculated']),
                'created': incident['Created'].isoformat() if pd.notna(incident['Created']) else None,
                'incident_id': incident['Number']
            })
    else:
        sla_candlestick_data = []
    
    return jsonify({
        'incident_trends': {
            'data': incident_data
        },
        'fcr_trends': {
            'data': fcr_data
        },
        'mttr_trends': {
            'data': mttr_data
        },
        'sla_trends': {
            'data': sla_data
        },
        'breach_trends': {
            'data': breach_data
        },
        'sla_candlestick_data': sla_candlestick_data,
        'quarter': quarter,
        'region': region
    })

@app.route('/api/team_performance')
def api_team_performance():
    """Get team performance data"""
    if incidents_df is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    quarter = request.args.get('quarter', 'all')  # Default to all data
    month = request.args.get('month', 'all')  # Default to all months
    region = request.args.get('region', 'all')   # Default to all regions
    assignment_group = request.args.get('assignment_group', 'all')   # Default to all groups
    
    # Apply filters
    filtered_df = apply_filters(incidents_df, quarter, month, region, assignment_group)
    
    # Group by assignment group
    # MTTR now uses business hours calculation, no need for weekday filtering
    team_stats = filtered_df.groupby('Assignment group').agg({
        'Number': 'count',
        'MTTR_calculated': 'mean',  # Business hours MTTR
        'Reopen count': lambda x: (x[x.notna()] == 0).sum() / x.notna().sum() * 100 if x.notna().sum() > 0 else 0,  # FCR with validation
        'sla_met_mttr': lambda x: (filtered_df.loc[x.index, 'sla_met_mttr']).sum() / len(x) * 100,  # SLA compliance based on MTTR
        'sla_met_goal': lambda x: (filtered_df.loc[x.index, 'sla_met_goal']).sum() / len(x) * 100,  # SLA goal compliance
        'sla_breached': lambda x: (filtered_df.loc[x.index, 'sla_breached']).sum()  # SLA breach count per team
    }).round(2)
    
    # Sort by incident count (descending) - show all teams
    team_stats_sorted = team_stats.sort_values('Number', ascending=False)
    
    team_performance = []
    for team, stats in team_stats_sorted.iterrows():
        # Clean team names more comprehensively
        clean_team = team
        clean_team = clean_team.replace('AEDT - Enterprise Tech Spot - ', '')
        clean_team = clean_team.replace('ADE - Enterprise Tech Spot - ', '')
        clean_team = clean_team.replace('ADE - Enterprise Tech Spot 2 - ', '')
        
        # Calculate critical breaches for this team (>240 mins over SLA)
        team_incidents = filtered_df[filtered_df['Assignment group'] == team]
        team_critical_breaches = len(team_incidents[(team_incidents['sla_breached'] == True) & (team_incidents['sla_variance_minutes'] > 240)])
        critical_breach_rate = (team_critical_breaches / stats['Number']) * 100 if stats['Number'] > 0 else 0
        
        team_performance.append({
            'team': clean_team,
            'incidents': int(stats['Number']),
            'avg_resolution_time': round(stats['MTTR_calculated'] / 60, 1) if not pd.isna(stats['MTTR_calculated']) else 0,
            'fcr_rate': round(stats['Reopen count'], 1),
            'sla_compliance_mttr': round(stats['sla_met_mttr'], 1),
            'sla_goal_compliance': round(stats['sla_met_goal'], 1),
            'sla_breaches': int(stats['sla_breached']),
            'sla_breach_rate': round((stats['sla_breached'] / stats['Number']) * 100, 1) if stats['Number'] > 0 else 0,
            'critical_breaches': int(team_critical_breaches),
            'critical_breach_rate': round(critical_breach_rate, 1)
        })
    
    return jsonify(team_performance)

@app.route('/api/sla_breach')
def api_sla_breach():
    """Get detailed SLA breach analysis"""
    if incidents_df is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    quarter = request.args.get('quarter', 'all')  # Default to all data
    month = request.args.get('month', 'all')  # Default to all months
    region = request.args.get('region', 'all')   # Default to all regions
    assignment_group = request.args.get('assignment_group', 'all')   # Default to all groups
    
    # Apply filters
    filtered_df = apply_filters(incidents_df, quarter, month, region, assignment_group)
    
    # Overall breach statistics
    total_incidents = len(filtered_df)
    total_breaches = (filtered_df['sla_breached'] == True).sum()
    breach_rate = (total_breaches / total_incidents) * 100 if total_incidents > 0 else 0
    
    # Severity analysis (breaches categorized by how severe they are)
    breach_incidents = filtered_df[filtered_df['sla_breached'] == True]
    if len(breach_incidents) > 0:
        moderate_breaches = len(breach_incidents[(breach_incidents['sla_variance_minutes'] > 180) & (breach_incidents['sla_variance_minutes'] <= 240)])  # >3hrs and ≤4hrs over SLA
        critical_breaches = len(breach_incidents[breach_incidents['sla_variance_minutes'] > 240])  # >4hrs over SLA
    else:
        moderate_breaches = critical_breaches = 0
    
    # Top breaching teams
    team_breach_stats = filtered_df.groupby('Assignment group').agg({
        'Number': 'count',
        'sla_breached': lambda x: (filtered_df.loc[x.index, 'sla_breached']).sum()
    }).round(2)
    team_breach_stats['breach_rate'] = (team_breach_stats['sla_breached'] / team_breach_stats['Number']) * 100
    
    # Monthly breach analysis
    monthly_breach_data = filtered_df.groupby(filtered_df['Created'].dt.to_period('M')).agg({
        'Number': 'count',
        'sla_breached': lambda x: (filtered_df.loc[x.index, 'sla_breached']).sum()
    }).round(2)
    monthly_breach_data['breach_rate'] = (monthly_breach_data['sla_breached'] / monthly_breach_data['Number']) * 100
    
    # Format response - get top breaching teams sorted by breach count
    top_breaching_teams = team_breach_stats.sort_values('sla_breached', ascending=False).head(10)
    top_teams = []
    for team, stats in top_breaching_teams.iterrows():
        clean_team = team.replace('AEDT - Enterprise Tech Spot - ', '').replace('ADE - Enterprise Tech Spot - ', '')
        top_teams.append({
            'team': clean_team,
            'incidents': int(stats['Number']),
            'breaches': int(stats['sla_breached']),
            'breach_rate': round(stats['breach_rate'], 1)
        })
    
    monthly_trends = []
    for period, stats in monthly_breach_data.iterrows():
        monthly_trends.append({
            'month': str(period),
            'incidents': int(stats['Number']),
            'breaches': int(stats['sla_breached']),
            'breach_rate': round(stats['breach_rate'], 1)
        })
    
    return jsonify({
        'summary': {
            'total_incidents': total_incidents,
            'total_breaches': int(total_breaches),  # Convert to regular Python int
            'breach_rate': round(breach_rate, 1),
            'sla_promise_hours': 4  # 240 minutes = 4 hours
        },
        'severity_breakdown': {
            'moderate_breaches': int(moderate_breaches),  # >3hrs and ≤4hrs over SLA
            'critical_breaches': int(critical_breaches)  # >4hrs over SLA
        },
        'top_breaching_teams': top_teams,
        'monthly_trends': monthly_trends,
        'quarter': quarter,
        'region': region
    })

@app.route('/api/team_drill_down')
def api_team_drill_down():
    """Get detailed drill-down data for a specific team"""
    if incidents_df is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    team_name = request.args.get('team', '')
    quarter = request.args.get('quarter', 'all')
    month = request.args.get('month', 'all')
    region = request.args.get('region', 'all')
    assignment_group = request.args.get('assignment_group', 'all')
    
    if not team_name:
        return jsonify({'error': 'Team name required'}), 400
    
    # Apply filters
    filtered_df = apply_filters(incidents_df, quarter, month, region, assignment_group)
    
    # Find the team with fuzzy matching (handle clean names from frontend)
    assignment_groups = filtered_df['Assignment group'].unique()
    matched_team = None
    
    print(f"DEBUG: Looking for team '{team_name}' in {len(assignment_groups)} assignment groups")
    
    for group in assignment_groups:
        # Clean the group name the same way as in team_performance endpoint
        clean_group = group
        clean_group = clean_group.replace('AEDT - Enterprise Tech Spot - ', '')
        clean_group = clean_group.replace('ADE - Enterprise Tech Spot - ', '')
        clean_group = clean_group.replace('ADE - Enterprise Tech Spot 2 - ', '')
        
        if ensure_tz_aware(clean_group) == ensure_tz_aware(team_name):
            matched_team = group
            print(f"DEBUG: Found match! '{team_name}' -> '{matched_team}'")
            break
    
    if not matched_team:
        print(f"DEBUG: No match found for '{team_name}'. Available clean names:")
        for group in assignment_groups[:10]:  # Show first 10 for debugging
            clean_group = group
            clean_group = clean_group.replace('AEDT - Enterprise Tech Spot - ', '')
            clean_group = clean_group.replace('ADE - Enterprise Tech Spot - ', '')
            clean_group = clean_group.replace('ADE - Enterprise Tech Spot 2 - ', '')
            print(f"  '{clean_group}' <- '{group}'")
        return jsonify({'error': f'Team "{team_name}" not found'}), 404
    
    # Filter data for this specific team
    team_df = filtered_df[filtered_df['Assignment group'] == matched_team]
    
    if len(team_df) == 0:
        return jsonify({'error': f'No data found for team "{team_name}" in selected quarter'}), 404
    
    # Calculate overall team metrics (using business hours calculation)
    total_incidents = len(team_df)
    print(f"DEBUG: Team '{team_name}' (matched to '{matched_team}') has {total_incidents} incidents")
    
    fcr_rate = (team_df['Reopen count'] == 0).sum() / total_incidents * 100 if total_incidents > 0 else 0
    avg_mttr = team_df['MTTR_calculated'].mean() if len(team_df) > 0 else 0  # Business hours MTTR
    sla_compliance = (team_df['sla_met_mttr'] == True).sum() / total_incidents * 100 if total_incidents > 0 else 0
    sla_goal_compliance = (team_df['sla_met_goal'] == True).sum() / total_incidents * 100 if total_incidents > 0 else 0
    
    # Calculate breach analysis
    sla_breaches = (team_df['sla_breached'] == True).sum()
    breach_incidents = team_df[team_df['sla_breached'] == True]
    
    if len(breach_incidents) > 0:
        critical_breaches = len(breach_incidents[breach_incidents['sla_variance_minutes'] > 240])  # >4hrs over SLA
        moderate_breaches = len(breach_incidents[(breach_incidents['sla_variance_minutes'] > 180) & (breach_incidents['sla_variance_minutes'] <= 240)])  # >3hrs and ≤4hrs over SLA
    else:
        critical_breaches = moderate_breaches = 0
    
    # Monthly breakdown (using business hours calculation)
    monthly_data = team_df.groupby(team_df['Created'].dt.to_period('M')).agg({
        'Number': 'count',
        'MTTR_calculated': 'mean',  # Business hours MTTR - no weekday filtering needed
        'Reopen count': lambda x: (x == 0).sum() / len(x) * 100,
        'sla_met_mttr': lambda x: (team_df.loc[x.index, 'sla_met_mttr']).sum() / len(x) * 100,
        'sla_met_goal': lambda x: (team_df.loc[x.index, 'sla_met_goal']).sum() / len(x) * 100,
    }).round(2)
    
    monthly_data = monthly_data.sort_index()
    
    # Prepare monthly labels and data
    monthly_labels = []
    monthly_incidents = []
    monthly_fcr = []
    monthly_mttr = []
    monthly_sla = []
    monthly_sla_goal = []
    
    for period, row in monthly_data.iterrows():
        month_name = period.strftime('%b')  # Feb, Mar, Apr, etc.
        monthly_labels.append(month_name)
        monthly_incidents.append(int(row['Number']))
        monthly_fcr.append(round(row['Reopen count'], 1))
        monthly_mttr.append(round(row['MTTR_calculated'] / 60, 1) if not pd.isna(row['MTTR_calculated']) else 0)  # Convert to hours
        monthly_sla.append(round(row['sla_met_mttr'], 1))
        monthly_sla_goal.append(round(row['sla_met_goal'], 1))
    
    # Highest SLA breach incidents (top 10 by resolution time)
    # Sort by MTTR descending to get the longest resolution times first
    highest_sla_incidents = team_df.nlargest(10, 'MTTR_calculated')[['Number', 'Created', 'MTTR_calculated', 'sla_breached', 'sla_variance_minutes']]
    recent_incidents_list = []
    
    for _, incident in highest_sla_incidents.iterrows():
        # Determine priority based on MTTR (since no Priority column exists)
        if ensure_tz_aware(incident['MTTR_calculated']) > ensure_tz_aware(480):  # > 8 hours
            priority = 'Critical'
        elif ensure_tz_aware(incident['MTTR_calculated']) > ensure_tz_aware(240):  # > 4 hours
            priority = 'High'
        elif ensure_tz_aware(incident['MTTR_calculated']) > ensure_tz_aware(120):  # > 2 hours
            priority = 'Medium'
        else:
            priority = 'Low'
        
        # Calculate days ago
        days_ago = (datetime.now(incident['Created'].tzinfo) - incident['Created']).days
        if ensure_tz_aware(days_ago) == ensure_tz_aware(0):
            created_text = 'Today'
        elif ensure_tz_aware(days_ago) == ensure_tz_aware(1):
            created_text = '1 day ago'
        else:
            created_text = f'{days_ago} days ago'
        
        # SLA status with more detailed breach classification
        if incident['sla_breached']:
            if ensure_tz_aware(incident['sla_variance_minutes']) > ensure_tz_aware(480):  # > 8 hours over SLA
                sla_status = 'Severe Breach'
            elif ensure_tz_aware(incident['sla_variance_minutes']) > ensure_tz_aware(240):  # > 4 hours over SLA
                sla_status = 'Critical Breach'
            elif ensure_tz_aware(incident['sla_variance_minutes']) > ensure_tz_aware(120):  # > 2 hours over SLA
                sla_status = 'Major Breach'
            else:
                sla_status = 'Minor Breach'
        else:
            sla_status = 'Met'
        
        # Calculate how much over SLA (for analysis)
        if incident['sla_breached']:
            variance_hours = round(incident['sla_variance_minutes'] / 60, 1)
            variance_text = f"+{variance_hours}h over SLA"
        else:
            variance_text = "Within SLA"
        
        recent_incidents_list.append({
            'id': incident['Number'],
            'priority': priority,
            'created': created_text,
            'resolution_time': f"{round(incident['MTTR_calculated'] / 60, 1)}h",
            'sla_status': sla_status,
            'sla_variance': variance_text,
            'mttr_minutes': round(incident['MTTR_calculated'], 0)  # For sorting/analysis
        })
    
    return jsonify({
        'team': team_name,
        'quarter': quarter,
        'region': region,
        'monthlyLabels': monthly_labels,
        'metrics': {
            'incidents': total_incidents,
            'fcr_rate': round(fcr_rate, 1),
            'avg_mttr': round(avg_mttr / 60, 1) if avg_mttr > 0 else 0,  # Convert to hours
            'sla_compliance': round(sla_compliance, 1),
            'sla_goal_compliance': round(sla_goal_compliance, 1),
            'critical_breaches': critical_breaches,
            'moderate_breaches': moderate_breaches
        },
        'monthly_incidents': monthly_incidents,
        'monthly_metrics': {
            'fcr': monthly_fcr,
            'mttr': monthly_mttr,
            'sla': monthly_sla,
            'sla_goal': monthly_sla_goal
        },
        'recent_incidents': recent_incidents_list
    })

@app.route('/api/incident_details')
def api_incident_details():
    """Get detailed information for a specific incident"""
    if incidents_df is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    try:
        incident_number = request.args.get('incident_number')
        if not incident_number:
            return jsonify({'error': 'Incident number is required'}), 400
        
        # Find the specific incident
        incident = incidents_df[incidents_df['Number'] == incident_number]
        if incident.empty:
            return jsonify({'error': 'Incident not found'}), 404
        
        incident = incident.iloc[0]
        
        # Calculate detailed metrics
        created_date = incident['Created']
        resolved_date = incident['Resolved']
        mttr_minutes = incident['MTTR_calculated']
        sla_breached = incident['sla_breached']
        sla_variance_minutes = incident['sla_variance_minutes']
        
        # Determine incident severity/priority based on MTTR
        if ensure_tz_aware(mttr_minutes) > ensure_tz_aware(480):  # > 8 hours
            priority = 'Critical'
            severity_level = 'P1 - Critical'
        elif ensure_tz_aware(mttr_minutes) > ensure_tz_aware(240):  # > 4 hours
            priority = 'High'
            severity_level = 'P2 - High'
        elif ensure_tz_aware(mttr_minutes) > ensure_tz_aware(120):  # > 2 hours
            priority = 'Medium'
            severity_level = 'P3 - Medium'
        else:
            priority = 'Low'
            severity_level = 'P4 - Low'
        
        # SLA status with detailed classification (updated for 4-hour baseline)
        if sla_breached:
            if ensure_tz_aware(sla_variance_minutes) > ensure_tz_aware(480):  # > 8 hours over SLA (> 2x baseline)
                sla_status = 'Severe Breach'
                sla_impact = 'Critical Impact'
            elif ensure_tz_aware(sla_variance_minutes) > ensure_tz_aware(300):  # > 5 hours over SLA  
                sla_status = 'Critical Breach'
                sla_impact = 'High Impact'
            elif ensure_tz_aware(sla_variance_minutes) > ensure_tz_aware(180):  # > 3 hours over SLA
                sla_status = 'Major Breach'
                sla_impact = 'Medium Impact'
            else:
                sla_status = 'Minor Breach'
                sla_impact = 'Low Impact'
        else:
            sla_status = 'Met'
            sla_impact = 'No Impact'
        
        # Calculate time breakdowns
        business_hours_only = created_date.weekday() < 5  # Monday=0, Sunday=6
        
        # Format times
        created_formatted = created_date.strftime('%Y-%m-%d %H:%M:%S')
        resolved_formatted = resolved_date.strftime('%Y-%m-%d %H:%M:%S') if pd.notna(resolved_date) else 'Not Resolved'
        
        # Calculate resolution time breakdown
        total_hours = round(mttr_minutes / 60, 2)
        total_days = round(mttr_minutes / (60 * 24), 2)
        
        # Real timeline based on actual data from Excel
        timeline = []
        
        # Initial report (real creation time)
        timeline.append({
            'timestamp': created_formatted,
            'event': 'Incident Reported',
            'description': f'Incident {incident_number} logged by {incident["Assignment group"]}',
            'status': 'completed'
        })
        
        # Resolution (real resolution time)
        if pd.notna(resolved_date):
            timeline.append({
                'timestamp': resolved_formatted,
                'event': 'Incident Resolved',
                'description': f'Incident successfully resolved after {total_hours} hours',
                'status': 'completed'
            })
        else:
            timeline.append({
                'timestamp': 'Pending',
                'event': 'Resolution Pending',
                'description': 'Incident resolution in progress',
                'status': 'pending'
            })
        
        # Real root cause analysis based on actual data patterns
        root_cause = f"Analysis based on real incident data: Resolution time was {total_hours} hours"
        if sla_breached:
            root_cause += f", exceeding SLA by {round(sla_variance_minutes/60, 1)} hours"
        else:
            root_cause += ", within SLA target"
        
        response = {
            'incident_number': incident_number,
            'basic_info': {
                'assignment_group': incident['Assignment group'],
                'priority': priority,
                'severity': severity_level,
                'created': created_formatted,
                'resolved': resolved_formatted,
                'status': str(incident['State']) if pd.notna(incident['State']) else ('Resolved' if pd.notna(resolved_date) else 'Open'),
                'opened_by': str(incident['Opened by']) if pd.notna(incident['Opened by']) else 'System',
                'resolved_by': str(incident['Resolved by']) if pd.notna(incident['Resolved by']) else 'N/A',
                'made_sla': bool(incident['Made SLA']) if pd.notna(incident['Made SLA']) else False
            },
            'tech_notes': {
                'work_notes': str(incident['Work notes']) if pd.notna(incident['Work notes']) and str(incident['Work notes']).strip() != '' else 'No work notes provided',
                'resolution_notes': str(incident['Resolution notes']) if pd.notna(incident['Resolution notes']) and str(incident['Resolution notes']).strip() != '' else 'No resolution notes provided',
                'knowledge_id': str(incident['Knowledge ID']) if pd.notna(incident['Knowledge ID']) and str(incident['Knowledge ID']).strip() != '' else 'No KB article referenced',
                'customer_description': str(incident['Description (Customer visible)']) if pd.notna(incident['Description (Customer visible)']) and str(incident['Description (Customer visible)']).strip() != '' else 'No customer description provided'
            },
            'timing_analysis': {
                'total_resolution_time': f"{total_hours} hours ({total_days} days)",
                'resolution_minutes': int(round(mttr_minutes, 0)),
                'business_hours_incident': bool(business_hours_only),
                'sla_target': '4 hours (240 minutes)',
                'sla_status': sla_status,
                'sla_impact': sla_impact,
                'sla_variance_minutes': int(round(sla_variance_minutes, 0)) if sla_breached else 0,
                'sla_variance_formatted': f"+{round(sla_variance_minutes/60, 1)} hours over SLA" if sla_breached else "Within SLA"
            },
            'timeline': timeline,
            'analysis': {
                'root_cause': root_cause,
                'impact_assessment': sla_impact,
                'incident_details': {
                    'assignment_group': str(incident['Assignment group']),
                    'reopen_count': int(incident['Reopen count']) if pd.notna(incident['Reopen count']) else 0,
                    'reassignment_count': int(incident['Reassignment count']) if pd.notna(incident['Reassignment count']) else 0,
                    'resolution_type': str(incident['Resolution Type']) if pd.notna(incident['Resolution Type']) else 'N/A',
                    'resolution_code': str(incident['Resolution code']) if pd.notna(incident['Resolution code']) else 'N/A',
                    'major_incident': bool(incident['Major incident']) if pd.notna(incident['Major incident']) else False,
                    'weekend_incident': bool(not business_hours_only),
                    'resolution_efficiency': 'High' if mttr_minutes < 60 else 'Medium' if mttr_minutes < 240 else 'Low',
                    'affected_application': str(incident['Affected application']) if pd.notna(incident['Affected application']) else 'N/A'
                },
                'lessons_learned': f"Real incident {incident_number}: {priority.lower()}-priority incident took {total_hours} hours to resolve, which {'exceeded' if sla_breached else 'met'} our SLA target of 4 hours."
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in incident_details: {str(e)}")
        return jsonify({'error': 'Failed to fetch incident details'}), 500

@app.route('/api/sla_breach_incidents')
def api_sla_breach_incidents():
    """Get incidents by SLA breach severity level - respects dashboard filters for contextual analysis"""
    if incidents_df is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    try:
        severity = request.args.get('severity', '')
        quarter = request.args.get('quarter', 'all')
        month = request.args.get('month', 'all')
        region = request.args.get('region', 'all')
        assignment_group = request.args.get('assignment_group', 'all')
        
        if not severity:
            return jsonify({'error': 'Severity level required'}), 400
        
        # Apply dashboard filters to show contextual SLA breaches
        filtered_df = apply_filters(incidents_df, quarter, month, region, assignment_group)
        
        # Get SLA breached incidents from filtered dataset
        breach_incidents = filtered_df[filtered_df['sla_breached'] == True]
        
        # Filter by severity level
        if severity.lower() == 'critical':
            # Critical: > 4 hours (240 minutes) over SLA
            severity_incidents = breach_incidents[breach_incidents['sla_variance_minutes'] > 240]
            severity_title = 'Critical SLA Breaches'
            severity_description = '>4 hours over SLA (>240 minutes over 4-hour baseline)'
        elif severity.lower() == 'moderate':
            # Moderate: >3 hours and ≤4 hours over SLA  
            severity_incidents = breach_incidents[
                (breach_incidents['sla_variance_minutes'] > 180) & 
                (breach_incidents['sla_variance_minutes'] <= 240)
            ]
            severity_title = 'Moderate SLA Breaches'
            severity_description = '>3 hours and ≤4 hours over SLA (180-240 minutes over 4-hour baseline)'
        else:
            return jsonify({'error': f'Invalid severity level: {severity}'}), 400
        
        if len(severity_incidents) == 0:
            return jsonify({
                'severity': severity.title(),
                'title': severity_title,
                'description': severity_description,
                'total_incidents': 0,
                'incidents': [],
                'quarter': 'all',  # Always show complete data
                'region': 'all'    # Always show complete data
            })
        
        # Sort by SLA variance (highest impact first)
        severity_incidents = severity_incidents.nlargest(50, 'sla_variance_minutes')
        
        # Prepare incident list
        incidents_list = []
        for _, incident in severity_incidents.iterrows():
            # Determine priority based on MTTR
            if ensure_tz_aware(incident['MTTR_calculated']) > ensure_tz_aware(480):  # > 8 hours
                priority = 'Critical'
            elif ensure_tz_aware(incident['MTTR_calculated']) > ensure_tz_aware(240):  # > 4 hours
                priority = 'High'
            elif ensure_tz_aware(incident['MTTR_calculated']) > ensure_tz_aware(180):  # > 3 hours  
                priority = 'Medium'
            else:
                priority = 'Low'
            
            # Calculate days ago
            days_ago = (datetime.now(incident['Created'].tzinfo) - incident['Created']).days
            if ensure_tz_aware(days_ago) == ensure_tz_aware(0):
                created_text = 'Today'
            elif ensure_tz_aware(days_ago) == ensure_tz_aware(1):
                created_text = '1 day ago'
            else:
                created_text = f'{days_ago} days ago'
            
            # Clean team name
            clean_team = incident['Assignment group']
            clean_team = clean_team.replace('AEDT - Enterprise Tech Spot - ', '')
            clean_team = clean_team.replace('ADE - Enterprise Tech Spot - ', '')
            clean_team = clean_team.replace('ADE - Enterprise Tech Spot 2 - ', '')
            
            # SLA variance text
            variance_hours = round(incident['sla_variance_minutes'] / 60, 1)
            variance_text = f"+{variance_hours}h over SLA"
            
            incidents_list.append({
                'id': incident['Number'],
                'priority': priority,
                'team': clean_team,
                'created': created_text,
                'created_date': incident['Created'].strftime('%Y-%m-%d %H:%M'),
                'resolution_time': f"{round(incident['MTTR_calculated'] / 60, 1)}h",
                'sla_variance': variance_text,
                'sla_variance_minutes': round(incident['sla_variance_minutes'], 0),
                'affected_application': str(incident['Affected application']) if pd.notna(incident['Affected application']) else 'N/A'
            })
        
        return jsonify({
            'severity': severity.title(),
            'title': severity_title,
            'description': severity_description,
            'total_incidents': len(severity_incidents),
            'incidents': incidents_list,
            'quarter': 'all',  # Always show complete data
            'region': 'all'    # Always show complete data
        })
        
    except Exception as e:
        print(f"Error in sla_breach_incidents: {str(e)}")
        return jsonify({'error': 'Failed to fetch SLA breach incidents'}), 500

@app.route('/api/mttr_drilldown')
def api_mttr_drilldown():
    """Get detailed MTTR analysis for a specific month"""
    if incidents_df is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    month = request.args.get('month')  # Format: "2025-02"
    region = request.args.get('region', 'all')
    assignment_group = request.args.get('assignment_group', 'all')
    
    if not month:
        return jsonify({'error': 'Month parameter required'}), 400
    
    # Apply region and assignment group filters but not time filters
    filtered_df = incidents_df.copy()
    
    # Apply region filter
    if region and region != 'all':
        filtered_df = filtered_df[filtered_df['Region'] == region]
    
    # Apply assignment group filter
    if assignment_group and assignment_group != 'all':
        filtered_df = filtered_df[filtered_df['Assignment group'] == assignment_group]
    
    # Filter by specific month
    # Use robust date parsing
    month_start, month_end = parse_month_parameter(month)
    
    if month_start is None or month_end is None:
        return jsonify({'error': f'Could not parse month format: {month}'}), 400
    
    month_df = filtered_df[
        (filtered_df['Created'] >= month_start) & 
        (filtered_df['Created'] <= month_end)
    ]
    
    if len(month_df) == 0:
        return jsonify({'error': f'No data found for month {month}'}), 404
    
    # Overall month statistics
    total_incidents = len(month_df)
    resolved_incidents = month_df[month_df['Resolved'].notna()]
    
    # Use business hours calculation (consistent with main dashboard)
    # No need for weekday filtering since business hours calculation already excludes weekend time
    avg_mttr = resolved_incidents['MTTR_calculated'].mean() if len(resolved_incidents) > 0 else 0
    
    # Quick vs Complex resolution analysis (using all resolved incidents with business hours calculation)
    quick_threshold = 60  # 1 hour in minutes
    medium_threshold = 180  # 3 hours in minutes
    
    quick_resolutions = resolved_incidents[resolved_incidents['MTTR_calculated'] <= quick_threshold]
    medium_resolutions = resolved_incidents[
        (resolved_incidents['MTTR_calculated'] > quick_threshold) & 
        (resolved_incidents['MTTR_calculated'] <= medium_threshold)
    ]
    complex_resolutions = resolved_incidents[resolved_incidents['MTTR_calculated'] > medium_threshold]
    
    # Top performing teams for this month (using business hours calculation)
    team_performance = month_df.groupby('Assignment group').agg({
        'Number': 'count',
        'MTTR_calculated': 'mean',  # Business hours MTTR - no weekday filtering needed
        'sla_met_mttr': lambda x: (month_df.loc[x.index, 'sla_met_mttr']).sum() / len(x) * 100
    }).round(2)
    
    # Sort by MTTR (ascending) to get best performing teams
    top_performers = team_performance.nsmallest(5, 'MTTR_calculated')
    
    # Sort by MTTR (descending) to get worst performing teams
    worst_performers = team_performance.nlargest(5, 'MTTR_calculated')
    
    # Prepare top performing teams data
    best_teams = []
    for team, stats in top_performers.iterrows():
        clean_team = team.replace('AEDT - Enterprise Tech Spot - ', '').replace('ADE - Enterprise Tech Spot - ', '').replace('ADE - Enterprise Tech Spot 2 - ', '')
        
        # Better formatting for very low MTTR values
        mttr_minutes = stats['MTTR_calculated']
        if ensure_tz_aware(mttr_minutes) < ensure_tz_aware(60):  # Less than 1 hour
            if ensure_tz_aware(mttr_minutes) < ensure_tz_aware(1):  # Less than 1 minute
                avg_mttr_display = f"{mttr_minutes:.1f}m"
            else:
                avg_mttr_display = f"{mttr_minutes:.0f}m"
        else:
            avg_mttr_display = f"{mttr_minutes/60:.1f}h"
        
        best_teams.append({
            'team': clean_team,
            'incidents': int(stats['Number']),
            'avg_mttr': avg_mttr_display,
            'avg_mttr_hours': round(stats['MTTR_calculated'] / 60, 2),  # Keep numeric value for sorting
            'sla_compliance': round(stats['sla_met_mttr'], 1)
        })
    
    # Prepare worst performing teams data
    worst_teams = []
    for team, stats in worst_performers.iterrows():
        clean_team = team.replace('AEDT - Enterprise Tech Spot - ', '').replace('ADE - Enterprise Tech Spot - ', '').replace('ADE - Enterprise Tech Spot 2 - ', '')
        
        # Format MTTR values for worst performing teams
        mttr_minutes = stats['MTTR_calculated']
        if ensure_tz_aware(mttr_minutes) < ensure_tz_aware(60):  # Less than 1 hour
            if ensure_tz_aware(mttr_minutes) < ensure_tz_aware(1):  # Less than 1 minute
                avg_mttr_display = f"{mttr_minutes:.1f}m"
            else:
                avg_mttr_display = f"{mttr_minutes:.0f}m"
        else:
            avg_mttr_display = f"{mttr_minutes/60:.1f}h"
        
        worst_teams.append({
            'team': clean_team,
            'incidents': int(stats['Number']),
            'avg_mttr': avg_mttr_display,
            'avg_mttr_hours': round(stats['MTTR_calculated'] / 60, 2),  # Keep numeric value for sorting
            'sla_compliance': round(stats['sla_met_mttr'], 1)
        })
    
    # Get specific incidents that contributed to the month's MTTR
    # Show a mix of quick and complex resolutions
    sample_quick = quick_resolutions.nsmallest(10, 'MTTR_calculated') if len(quick_resolutions) > 0 else pd.DataFrame()
    sample_complex = complex_resolutions.nlargest(10, 'MTTR_calculated') if len(complex_resolutions) > 0 else pd.DataFrame()
    
    incident_details = []
    
    # Add quick resolution examples
    for _, incident in sample_quick.iterrows():
        incident_details.append({
            'incident_id': incident['Number'],
            'mttr_minutes': round(incident['MTTR_calculated'], 0),
            'mttr_hours': round(incident['MTTR_calculated'] / 60, 1),
            'category': 'Quick Resolution',
            'assignment_group': incident['Assignment group'],
            'knowledge_used': 'Yes' if pd.notna(incident['Knowledge ID']) and str(incident['Knowledge ID']).strip() != '' else 'No',
            'reopen_count': int(incident['Reopen count']) if pd.notna(incident['Reopen count']) else 0,
            'resolved_by': str(incident['Resolved by']) if pd.notna(incident['Resolved by']) else 'Unknown'
        })
    
    # Add complex resolution examples
    for _, incident in sample_complex.iterrows():
        incident_details.append({
            'incident_id': incident['Number'],
            'mttr_minutes': round(incident['MTTR_calculated'], 0),
            'mttr_hours': round(incident['MTTR_calculated'] / 60, 1),
            'category': 'Complex Resolution',
            'assignment_group': incident['Assignment group'],
            'knowledge_used': 'Yes' if pd.notna(incident['Knowledge ID']) and str(incident['Knowledge ID']).strip() != '' else 'No',
            'reopen_count': int(incident['Reopen count']) if pd.notna(incident['Reopen count']) else 0,
            'resolved_by': str(incident['Resolved by']) if pd.notna(incident['Resolved by']) else 'Unknown'
        })
    
    # Goal Achievement Analysis
    sla_goal_threshold = 192  # 3.2 hours in minutes
    sla_baseline_threshold = 240  # 4.0 hours in minutes
    exceeding_threshold = 120  # 2.0 hours in minutes
    
    # SLA Goal Achievement (3.2 hours) - using business hours calculation
    sla_goal_met = resolved_incidents[resolved_incidents['MTTR_calculated'] <= sla_goal_threshold]
    sla_goal_count = len(sla_goal_met)
    sla_goal_rate = round(sla_goal_count / len(resolved_incidents) * 100, 1) if len(resolved_incidents) > 0 else 0
    
    # SLA Baseline Compliance (4.0 hours) - using business hours calculation
    sla_baseline_met = resolved_incidents[resolved_incidents['MTTR_calculated'] <= sla_baseline_threshold]
    sla_baseline_count = len(sla_baseline_met)
    sla_baseline_rate = round(sla_baseline_count / len(resolved_incidents) * 100, 1) if len(resolved_incidents) > 0 else 0
    
    # Performance Categories - using business hours calculation
    exceeding_goals = resolved_incidents[resolved_incidents['MTTR_calculated'] <= exceeding_threshold]
    meeting_goals = resolved_incidents[
        (resolved_incidents['MTTR_calculated'] > exceeding_threshold) & 
        (resolved_incidents['MTTR_calculated'] <= sla_goal_threshold)
    ]
    missing_goals = resolved_incidents[resolved_incidents['MTTR_calculated'] > sla_goal_threshold]
    
    goal_analysis = {
        'sla_goal_rate': sla_goal_rate,
        'sla_goal_count': sla_goal_count,
        'sla_baseline_rate': sla_baseline_rate,
        'sla_baseline_count': sla_baseline_count,
        'exceeding_goals': {
            'count': len(exceeding_goals),
            'avg_mttr': round(exceeding_goals['MTTR_calculated'].mean() / 60, 1) if len(exceeding_goals) > 0 else 0
        },
        'meeting_goals': {
            'count': len(meeting_goals),
            'avg_mttr': round(meeting_goals['MTTR_calculated'].mean() / 60, 1) if len(meeting_goals) > 0 else 0
        },
        'missing_goals': {
            'count': len(missing_goals),
            'avg_mttr': round(missing_goals['MTTR_calculated'].mean() / 60, 1) if len(missing_goals) > 0 else 0
        }
    }
    
    return jsonify({
        'month': month,
        'month_name': month_start.strftime('%B %Y'),
        'summary': {
            'total_incidents': total_incidents,
            'resolved_incidents': len(resolved_incidents),
            'avg_mttr_hours': round(avg_mttr / 60, 1),
            'avg_mttr_minutes': round(avg_mttr, 0)
        },
        'resolution_breakdown': {
            'quick': {
                'count': len(quick_resolutions),
                'percentage': round(len(quick_resolutions) / len(resolved_incidents) * 100, 1) if len(resolved_incidents) > 0 else 0,
                'avg_mttr': round(quick_resolutions['MTTR_calculated'].mean() / 60, 1) if len(quick_resolutions) > 0 else 0,
                'description': f'{len(quick_resolutions)} incidents resolved under 1 hour'
            },
            'medium': {
                'count': len(medium_resolutions),
                'percentage': round(len(medium_resolutions) / len(resolved_incidents) * 100, 1) if len(resolved_incidents) > 0 else 0,
                'avg_mttr': round(medium_resolutions['MTTR_calculated'].mean() / 60, 1) if len(medium_resolutions) > 0 else 0,
                'description': f'{len(medium_resolutions)} incidents resolved in 1-3 hours'
            },
            'complex': {
                'count': len(complex_resolutions),
                'percentage': round(len(complex_resolutions) / len(resolved_incidents) * 100, 1) if len(resolved_incidents) > 0 else 0,
                'avg_mttr': round(complex_resolutions['MTTR_calculated'].mean() / 60, 1) if len(complex_resolutions) > 0 else 0,
                'description': f'{len(complex_resolutions)} incidents took over 3 hours'
            }
        },
        'goal_analysis': goal_analysis,
        'best_performing_teams': best_teams,
        'worst_performing_teams': worst_teams,
        'incident_samples': incident_details,
        'insights': {
            'primary_factor': 'Exceeding Goals' if len(exceeding_goals) > len(missing_goals) else 'Missing Goals',
            'goal_achievement': 'Excellent' if goal_analysis['sla_goal_rate'] >= 95 else 'Good' if goal_analysis['sla_goal_rate'] >= 85 else 'Needs Improvement',
            'team_consistency': 'High' if len(best_teams) > 0 and best_teams[0]['avg_mttr_hours'] < 2 else 'Moderate'
        }
    })

@app.route('/api/incident_drilldown')
def api_incident_drilldown():
    """Get detailed incident analysis for a specific month"""
    if incidents_df is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    month = request.args.get('month')  # Format: "2025-02"
    region = request.args.get('region', 'all')
    assignment_group = request.args.get('assignment_group', 'all')
    
    if not month:
        return jsonify({'error': 'Month parameter required'}), 400
    
    # Apply region and assignment group filters but not time filters
    filtered_df = incidents_df.copy()
    
    # Apply region filter
    if region and region != 'all':
        filtered_df = filtered_df[filtered_df['Region'] == region]
    
    # Apply assignment group filter
    if assignment_group and assignment_group != 'all':
        filtered_df = filtered_df[filtered_df['Assignment group'] == assignment_group]
    
    # Filter by specific month
    # Use robust date parsing
    month_start, month_end = parse_month_parameter(month)
    
    if month_start is None or month_end is None:
        return jsonify({'error': f'Could not parse month format: {month}'}), 400
    
    month_df = filtered_df[
        (filtered_df['Created'] >= month_start) & 
        (filtered_df['Created'] <= month_end)
    ]
    
    if len(month_df) == 0:
        return jsonify({'error': 'No data for selected month'}), 404
    
    # Most affected applications/services
    # Use Description field to identify common issues
    affected_apps = []
    if 'Description (Customer visible)' in month_df.columns:
        descriptions = month_df['Description (Customer visible)'].dropna()
        # Extract common keywords or patterns
        common_issues = {}
        for desc in descriptions:
            desc_lower = str(desc).lower()
            # Common issue categories
            if 'laptop' in desc_lower or 'computer' in desc_lower:
                common_issues['Hardware Issues'] = common_issues.get('Hardware Issues', 0) + 1
            elif 'software' in desc_lower or 'application' in desc_lower:
                common_issues['Software Issues'] = common_issues.get('Software Issues', 0) + 1
            elif 'network' in desc_lower or 'wifi' in desc_lower or 'connectivity' in desc_lower:
                common_issues['Network/Connectivity'] = common_issues.get('Network/Connectivity', 0) + 1
            elif 'password' in desc_lower or 'login' in desc_lower or 'authentication' in desc_lower:
                common_issues['Authentication Issues'] = common_issues.get('Authentication Issues', 0) + 1
            elif 'printer' in desc_lower or 'print' in desc_lower:
                common_issues['Printer Issues'] = common_issues.get('Printer Issues', 0) + 1
            else:
                common_issues['Other Issues'] = common_issues.get('Other Issues', 0) + 1
        
        # Convert to list sorted by count
        for issue_type, count in sorted(common_issues.items(), key=lambda x: x[1], reverse=True)[:10]:
            percentage = (count / len(month_df) * 100)
            affected_apps.append({
                'name': issue_type,
                'count': int(count),
                'percentage': round(percentage, 1)
            })
    
    # Top KB articles used
    kb_data = month_df[month_df['Knowledge ID'].notna()]
    top_kb_articles = []
    
    if len(kb_data) > 0:
        kb_counts = kb_data['Knowledge ID'].value_counts().head(10)
        
        for kb_id, count in kb_counts.items():
            percentage = (count / len(month_df) * 100)
            
            # Get issue description for this KB ID
            kb_incidents = kb_data[kb_data['Knowledge ID'] == kb_id]
            descriptions = kb_incidents['Description (Customer visible)'].dropna()
            
            # Create smart titles based on KB ID
            if 'KB1149657' in kb_id:
                issue_description = "End of Life (EOL) Laptop Returns & Replacements"
            elif 'KB1148221' in kb_id:
                issue_description = "Wireless Mouse Pairing & Connection Issues"
            elif 'KB1148390' in kb_id:
                issue_description = "Hardware Troubleshooting & BIOS Updates"
            elif 'KB1148222' in kb_id:
                issue_description = "User Account & Authentication Issues"
            elif 'KB1143222' in kb_id:
                issue_description = "Machine Hotswap & User Transfers"
            elif 'KB1146152' in kb_id:
                issue_description = "Network Connectivity & WIFI Issues"
            elif 'KB1150423' in kb_id:
                issue_description = "System Performance & Optimization"
            elif 'KB1148224' in kb_id:
                issue_description = "Software Installation & Configuration"
            elif 'KB1148665' in kb_id:
                issue_description = "Hardware Diagnostics & Repair"
            elif 'KB1148636' in kb_id:
                issue_description = "Device Setup & Initial Configuration"
            else:
                # Try to extract from descriptions
                if len(descriptions) > 0:
                    all_text = ' '.join(descriptions.astype(str).str.lower())
                    if 'mouse' in all_text or 'wireless' in all_text:
                        issue_description = "Wireless Device Connection Issues"
                    elif 'laptop' in all_text or 'computer' in all_text:
                        issue_description = "Laptop & Computer Hardware Issues"
                    elif 'wifi' in all_text or 'network' in all_text:
                        issue_description = "Network & Connectivity Issues"
                    elif 'password' in all_text or 'login' in all_text:
                        issue_description = "Authentication & Access Issues"
                    elif 'software' in all_text or 'application' in all_text:
                        issue_description = "Software & Application Issues"
                    else:
                        issue_description = "Technical Support Issue"
                else:
                    issue_description = "Technical Support Issue"
            
            top_kb_articles.append({
                'kb_id': kb_id,
                'description': issue_description,
                'count': int(count),
                'percentage': round(percentage, 1)
            })
    
    # Major vs routine incidents (based on MTTR)
    major_threshold = 240  # 4 hours in minutes
    major_incidents = month_df[month_df['MTTR_calculated'] > major_threshold]
    routine_incidents = month_df[month_df['MTTR_calculated'] <= major_threshold]
    
    # Regional distribution
    regional_dist = []
    if 'mapped_region' in month_df.columns:
        region_counts = month_df['mapped_region'].value_counts()
        for region, count in region_counts.items():
            percentage = (count / len(month_df) * 100)
            regional_dist.append({
                'region': region,
                'count': int(count),
                'percentage': round(percentage, 1)
            })
    
    # Day of week analysis
    dow_counts = month_df['Created'].dt.day_name().value_counts()
    daily_patterns = []
    for day, count in dow_counts.items():
        percentage = (count / len(month_df) * 100)
        daily_patterns.append({
            'day': day,
            'count': int(count),
            'percentage': round(percentage, 1)
        })
    
    # Peak times analysis (hour of day)
    hour_counts = month_df['Created'].dt.hour.value_counts().sort_index()
    peak_hours = []
    for hour, count in hour_counts.items():
        peak_hours.append({
            'hour': hour,
            'count': int(count)
        })
    
    # Sample critical incidents
    critical_incidents = month_df.nlargest(5, 'MTTR_calculated')[
        ['Number', 'Description (Customer visible)', 'MTTR_calculated', 'Assignment group', 'Created']
    ]
    
    incident_samples = []
    for _, incident in critical_incidents.iterrows():
        incident_samples.append({
            'number': incident['Number'],
            'description': str(incident['Description (Customer visible)'])[:200] + '...' if len(str(incident['Description (Customer visible)'])) > 200 else str(incident['Description (Customer visible)']),
            'mttr_hours': round(incident['MTTR_calculated'] / 60, 1),
            'team': incident['Assignment group'],
            'created': incident['Created'].strftime('%Y-%m-%d %H:%M')
        })
    
    # Calculate insights
    total_incidents = len(month_df)
    avg_daily = total_incidents / month_df['Created'].dt.day.nunique()
    
    return jsonify({
        'total_incidents': total_incidents,
        'affected_applications': affected_apps,
        'top_kb_articles': top_kb_articles,
        'incident_breakdown': {
            'major': {
                'count': len(major_incidents),
                'percentage': round(len(major_incidents) / total_incidents * 100, 1) if total_incidents > 0 else 0,
                'avg_mttr': round(major_incidents['MTTR_calculated'].mean() / 60, 1) if len(major_incidents) > 0 else 0
            },
            'routine': {
                'count': len(routine_incidents),
                'percentage': round(len(routine_incidents) / total_incidents * 100, 1) if total_incidents > 0 else 0,
                'avg_mttr': round(routine_incidents['MTTR_calculated'].mean() / 60, 1) if len(routine_incidents) > 0 else 0
            }
        },
        'critical_incidents': incident_samples,
        'insights': {
            'avg_daily_incidents': round(avg_daily, 1),
            'major_incident_ratio': 'High' if len(major_incidents) / total_incidents > 0.2 else 'Normal' if len(major_incidents) / total_incidents > 0.1 else 'Low',
            'kb_coverage': round((len(kb_data) / total_incidents * 100), 1) if total_incidents > 0 else 0,
            'unique_kb_articles': month_df['Knowledge ID'].nunique()
        }
    })

@app.route('/api/application_drilldown')
def api_application_drilldown():
    """Get detailed incident analysis for a specific application/service type"""
    if incidents_df is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    try:
        # Get parameters
        month = request.args.get('month')
        application_type = request.args.get('application_type')
        
        if not month or not application_type:
            return jsonify({'error': 'Month and application_type parameters required'}), 400
        
        # Parse the month
        try:
            target_date = pd.to_datetime(month)
        except:
            return jsonify({'error': 'Invalid date format'}), 400
        
        # Filter incidents by month
        month_df = incidents_df[
            (incidents_df['Created'].dt.year == target_date.year) &
            (incidents_df['Created'].dt.month == target_date.month)
        ].copy()
        
        if len(month_df) == 0:
            return jsonify({'error': 'No incidents found for this month'}), 404
        
        # Filter incidents by application type based on description keywords
        application_incidents = []
        descriptions = month_df['Description (Customer visible)'].dropna()
        
        for idx, row in month_df.iterrows():
            if pd.isna(row.get('Description (Customer visible)')):
                continue
                
            desc_lower = str(row['Description (Customer visible)']).lower()
            matches_type = False
            
            # Match incidents based on application type
            if application_type == 'Hardware Issues':
                matches_type = 'laptop' in desc_lower or 'computer' in desc_lower
            elif application_type == 'Software Issues':
                matches_type = 'software' in desc_lower or 'application' in desc_lower
            elif application_type == 'Network/Connectivity':
                matches_type = 'network' in desc_lower or 'wifi' in desc_lower or 'connectivity' in desc_lower
            elif application_type == 'Authentication Issues':
                matches_type = 'password' in desc_lower or 'login' in desc_lower or 'authentication' in desc_lower
            elif application_type == 'Printer Issues':
                matches_type = 'printer' in desc_lower or 'print' in desc_lower
            elif application_type == 'Other Issues':
                matches_type = not any([
                    'laptop' in desc_lower, 'computer' in desc_lower,
                    'software' in desc_lower, 'application' in desc_lower,
                    'network' in desc_lower, 'wifi' in desc_lower, 'connectivity' in desc_lower,
                    'password' in desc_lower, 'login' in desc_lower, 'authentication' in desc_lower,
                    'printer' in desc_lower, 'print' in desc_lower
                ])
            
            if matches_type:
                application_incidents.append({
                    'incident_number': row['Number'],
                    'created_date': row['Created'].strftime('%Y-%m-%d %H:%M'),
                    'resolved_date': row['Resolved'].strftime('%Y-%m-%d %H:%M') if pd.notna(row['Resolved']) else 'Not Resolved',
                    'assignment_group': row['Assignment group'],
                    'state': row['State'],
                    'priority': row.get('Priority', 'N/A'),
                    'description': str(row['Description (Customer visible)'])[:200] + '...' if len(str(row['Description (Customer visible)'])) > 200 else str(row['Description (Customer visible)']),
                    'mttr_minutes': round(row['MTTR_calculated'], 1) if pd.notna(row['MTTR_calculated']) else None,
                    'sla_met': bool(row.get('Made SLA', False)),
                    'reopen_count': int(row.get('Reopen count', 0)) if pd.notna(row.get('Reopen count', 0)) else 0
                })
        
        # Calculate summary statistics
        if len(application_incidents) > 0:
            filtered_df = month_df[month_df.index.isin([incident['incident_number'] for incident in application_incidents])]
            
            # MTTR statistics
            resolved_incidents = [inc for inc in application_incidents if inc['mttr_minutes'] is not None]
            avg_mttr = sum([inc['mttr_minutes'] for inc in resolved_incidents]) / len(resolved_incidents) if resolved_incidents else 0
            
            # SLA statistics
            sla_met_count = sum([1 for inc in application_incidents if inc['sla_met']])
            sla_rate = (sla_met_count / len(application_incidents)) * 100
            
            # Assignment group breakdown
            group_counts = {}
            for incident in application_incidents:
                group = incident['assignment_group']
                group_counts[group] = group_counts.get(group, 0) + 1
            
            top_groups = sorted(group_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            summary = {
                'total_incidents': len(application_incidents),
                'avg_mttr_hours': round(avg_mttr / 60, 1) if avg_mttr > 0 else 0,
                'sla_compliance_rate': round(sla_rate, 1),
                'resolved_incidents': len(resolved_incidents),
                'pending_incidents': len(application_incidents) - len(resolved_incidents),
                'top_assignment_groups': [{'group': group, 'count': count} for group, count in top_groups]
            }
        else:
            summary = {
                'total_incidents': 0,
                'avg_mttr_hours': 0,
                'sla_compliance_rate': 0,
                'resolved_incidents': 0,
                'pending_incidents': 0,
                'top_assignment_groups': []
            }
        
        return jsonify({
            'application_type': application_type,
            'month': month,
            'summary': summary,
            'incidents': application_incidents[:50]  # Limit to 50 most recent incidents
        })
        
    except Exception as e:
        print(f"Error in application_drilldown: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/fcr_drilldown')
def api_fcr_drilldown():
    """Get detailed FCR analysis for a specific month"""
    if incidents_df is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    month = request.args.get('month')  # Format: "2025-02"
    region = request.args.get('region', 'all')
    assignment_group = request.args.get('assignment_group', 'all')
    
    if not month:
        return jsonify({'error': 'Month parameter required'}), 400
    
    # Apply region and assignment group filters but not time filters
    filtered_df = incidents_df.copy()
    
    # Apply region filter
    if region and region != 'all':
        filtered_df = filtered_df[filtered_df['Region'] == region]
    
    # Apply assignment group filter
    if assignment_group and assignment_group != 'all':
        filtered_df = filtered_df[filtered_df['Assignment group'] == assignment_group]
    
    # Filter by specific month
    # Use robust date parsing
    month_start, month_end = parse_month_parameter(month)
    
    if month_start is None or month_end is None:
        return jsonify({'error': f'Could not parse month format: {month}'}), 400
    
    month_df = filtered_df[
        (filtered_df['Created'] >= month_start) & 
        (filtered_df['Created'] <= month_end)
    ]
    
    if len(month_df) == 0:
        return jsonify({'error': 'No data for selected month'}), 404
    
    # Calculate FCR metrics for the month
    valid_data = month_df[pd.to_numeric(month_df['Reopen count'], errors='coerce').notna()]
    reopened_incidents = valid_data[pd.to_numeric(valid_data['Reopen count'], errors='coerce') > 0]
    fcr_success = valid_data[pd.to_numeric(valid_data['Reopen count'], errors='coerce') == 0]
    
    total_valid = len(valid_data)
    fcr_rate = (len(fcr_success) / total_valid * 100) if total_valid > 0 else 0
    
    # Top reasons for reopens (analyze from descriptions of reopened incidents)
    reopen_reasons = []
    if len(reopened_incidents) > 0:
        # Group by assignment group to identify problematic areas
        reopen_by_group = reopened_incidents['Assignment group'].value_counts().head(10)
        for group, count in reopen_by_group.items():
            percentage = (count / len(reopened_incidents) * 100)
            reopen_reasons.append({
                'reason': f'Issues from {group}',
                'count': int(count),
                'percentage': round(percentage, 1)
            })
    
    # Teams with best/worst FCR rates
    team_fcr = []
    for team in valid_data['Assignment group'].unique():
        team_data = valid_data[valid_data['Assignment group'] == team]
        if len(team_data) >= 5:  # Only include teams with at least 5 incidents
            team_fcr_success = team_data[pd.to_numeric(team_data['Reopen count'], errors='coerce') == 0]
            team_fcr_rate = (len(team_fcr_success) / len(team_data) * 100)
            team_fcr.append({
                'team': team,
                'fcr_rate': round(team_fcr_rate, 1),
                'total_incidents': len(team_data),
                'successful_fcr': len(team_fcr_success)
            })
    
    # Sort teams by FCR rate
    team_fcr_sorted = sorted(team_fcr, key=lambda x: x['fcr_rate'], reverse=True)
    best_teams = team_fcr_sorted[:5]
    worst_teams = team_fcr_sorted[-5:] if len(team_fcr_sorted) > 5 else []
    
    # Incident types with highest FCR success
    # Use Description field to categorize incident types
    incident_type_fcr = []
    if 'Description (Customer visible)' in valid_data.columns:
        # Categorize incidents by type based on descriptions
        incident_categories = {}
        for _, incident in valid_data.iterrows():
            desc_lower = str(incident['Description (Customer visible)']).lower()
            # Categorize based on common keywords
            if 'hardware' in desc_lower or 'laptop' in desc_lower or 'computer' in desc_lower:
                category = 'Hardware Issues'
            elif 'software' in desc_lower or 'application' in desc_lower or 'install' in desc_lower:
                category = 'Software Issues'
            elif 'network' in desc_lower or 'wifi' in desc_lower or 'connectivity' in desc_lower:
                category = 'Network Issues'
            elif 'password' in desc_lower or 'login' in desc_lower or 'authentication' in desc_lower:
                category = 'Authentication Issues'
            elif 'printer' in desc_lower or 'print' in desc_lower:
                category = 'Printer Issues'
            elif 'email' in desc_lower or 'outlook' in desc_lower:
                category = 'Email Issues'
            else:
                category = 'Other Issues'
            
            if category not in incident_categories:
                incident_categories[category] = {'total': 0, 'fcr_success': 0}
            
            incident_categories[category]['total'] += 1
            if pd.to_numeric(incident['Reopen count'], errors='coerce') == 0:
                incident_categories[category]['fcr_success'] += 1
        
        # Calculate FCR rates for each category
        for category, counts in incident_categories.items():
            if ensure_tz_aware(counts['total']) >= ensure_tz_aware(3):  # Only include categories with at least 3 incidents
                fcr_rate = (counts['fcr_success'] / counts['total'] * 100)
                incident_type_fcr.append({
                    'symptom': category,  # Keep key name for compatibility
                    'fcr_rate': round(fcr_rate, 1),
                    'total_incidents': counts['total']
                })
    
    incident_type_fcr_sorted = sorted(incident_type_fcr, key=lambda x: x['fcr_rate'], reverse=True)
    
    # KB usage correlation with FCR
    kb_analysis = {
        'with_kb': {
            'total': 0,
            'fcr_success': 0,
            'fcr_rate': 0
        },
        'without_kb': {
            'total': 0,
            'fcr_success': 0,
            'fcr_rate': 0
        }
    }
    
    kb_incidents = valid_data[valid_data['Knowledge ID'].notna()]
    no_kb_incidents = valid_data[valid_data['Knowledge ID'].isna()]
    
    if len(kb_incidents) > 0:
        kb_fcr_success = kb_incidents[pd.to_numeric(kb_incidents['Reopen count'], errors='coerce') == 0]
        kb_analysis['with_kb'] = {
            'total': len(kb_incidents),
            'fcr_success': len(kb_fcr_success),
            'fcr_rate': round(len(kb_fcr_success) / len(kb_incidents) * 100, 1)
        }
    
    if len(no_kb_incidents) > 0:
        no_kb_fcr_success = no_kb_incidents[pd.to_numeric(no_kb_incidents['Reopen count'], errors='coerce') == 0]
        kb_analysis['without_kb'] = {
            'total': len(no_kb_incidents),
            'fcr_success': len(no_kb_fcr_success),
            'fcr_rate': round(len(no_kb_fcr_success) / len(no_kb_incidents) * 100, 1)
        }
    
    # Sample reopened incidents
    sample_reopened = reopened_incidents.nlargest(5, 'Reopen count')[
        ['Number', 'Description (Customer visible)', 'Reopen count', 'Assignment group', 'Created']
    ]
    
    reopened_samples = []
    for _, incident in sample_reopened.iterrows():
        reopened_samples.append({
            'number': incident['Number'],
            'description': str(incident['Description (Customer visible)'])[:200] + '...' if len(str(incident['Description (Customer visible)'])) > 200 else str(incident['Description (Customer visible)']),
            'reopen_count': int(incident['Reopen count']),
            'team': incident['Assignment group'],
            'created': incident['Created'].strftime('%Y-%m-%d %H:%M')
        })
    
    return jsonify({
        'total_incidents': total_valid,
        'fcr_rate': round(fcr_rate, 1),
        'successful_fcr': len(fcr_success),
        'reopened_incidents': len(reopened_incidents),
        'reopen_reasons': reopen_reasons,
        'best_performing_teams': best_teams,
        'worst_performing_teams': worst_teams,
        'incident_types_fcr': incident_type_fcr_sorted[:10],
        'kb_impact': kb_analysis,
        'reopened_samples': reopened_samples,
        'insights': {
            'kb_effectiveness': 'High' if kb_analysis['with_kb']['fcr_rate'] > kb_analysis['without_kb']['fcr_rate'] else 'Low',
            'fcr_trend': 'Good' if fcr_rate > 90 else 'Needs Improvement' if fcr_rate > 80 else 'Critical',
            'team_variance': 'High' if len(team_fcr) > 0 and (max(t['fcr_rate'] for t in team_fcr) - min(t['fcr_rate'] for t in team_fcr)) > 20 else 'Normal'
        }
    })

@app.route('/api/kb_trending')
def api_kb_trending():
    """Get trending Knowledge Base articles usage data"""
    try:
        quarter = request.args.get('quarter', 'all')
        month = request.args.get('month', 'all')
        region = request.args.get('region', 'all')
        assignment_group = request.args.get('assignment_group', 'all')
        
        filtered_df = apply_filters(incidents_df, quarter, month, region, assignment_group)
        
        # Analyze Knowledge Base usage
        kb_data = filtered_df[filtered_df['Knowledge ID'].notna()]
        
        # Top KB articles by usage count
        top_kb_articles = kb_data['Knowledge ID'].value_counts().head(10)
        
        # KB coverage and metrics
        total_incidents = len(filtered_df)
        kb_covered_incidents = len(kb_data)
        kb_coverage = (kb_covered_incidents / total_incidents * 100) if total_incidents > 0 else 0
        unique_kb_count = kb_data['Knowledge ID'].nunique()
        
        # Monthly trend of KB usage
        monthly_kb_trends = kb_data.groupby(kb_data['Created'].dt.to_period('M')).agg({
            'Knowledge ID': 'count',
            'Number': 'count'
        }).round(2)
        
        # Resolution type correlation with KB usage
        resolution_type_kb = kb_data['Resolution Type'].value_counts().head(5)
        
        # Format data for charts with meaningful descriptions
        kb_articles_data = []
        for kb_id, count in top_kb_articles.items():
            percentage = (count / total_incidents * 100) if total_incidents > 0 else 0
            
            # Generate a meaningful title for this KB ID based on common issue patterns
            kb_incidents = kb_data[kb_data['Knowledge ID'] == kb_id]
            if len(kb_incidents) > 0:
                # Get sample descriptions to analyze patterns
                descriptions = kb_incidents['Description (Customer visible)'].dropna()
                if len(descriptions) > 0:
                    # Analyze descriptions to create a meaningful title
                    all_text = ' '.join(descriptions.astype(str).str.lower())
                    
                    # Create smart titles based on KB ID and common patterns
                    if 'KB1149657' in kb_id:
                        issue_description = "End of Life (EOL) Laptop Returns & Replacements"
                    elif 'KB1148221' in kb_id:
                        issue_description = "Wireless Mouse Pairing & Connection Issues"
                    elif 'KB1148390' in kb_id:
                        issue_description = "Hardware Troubleshooting & BIOS Updates"
                    elif 'KB1148222' in kb_id:
                        issue_description = "User Account & Authentication Issues"
                    elif 'KB1143222' in kb_id:
                        issue_description = "Machine Hotswap & User Transfers"
                    elif 'KB1146152' in kb_id:
                        issue_description = "Network Connectivity & WIFI Issues"
                    elif 'KB1150423' in kb_id:
                        issue_description = "System Performance & Optimization"
                    elif 'KB1148224' in kb_id:
                        issue_description = "Software Installation & Configuration"
                    elif 'KB1148665' in kb_id:
                        issue_description = "Hardware Diagnostics & Repair"
                    elif 'KB1148636' in kb_id:
                        issue_description = "Device Setup & Initial Configuration"
                    # Fallback: try to extract meaningful keywords
                    elif 'mouse' in all_text or 'wireless' in all_text:
                        issue_description = "Wireless Device Connection Issues"
                    elif 'laptop' in all_text or 'computer' in all_text:
                        issue_description = "Laptop & Computer Hardware Issues"
                    elif 'wifi' in all_text or 'network' in all_text:
                        issue_description = "Network & Connectivity Issues"
                    elif 'password' in all_text or 'login' in all_text:
                        issue_description = "Authentication & Access Issues"
                    elif 'software' in all_text or 'application' in all_text:
                        issue_description = "Software & Application Issues"
                    else:
                        # Extract a clean sample from most common description
                        most_common_desc = descriptions.value_counts().index[0]
                        clean_desc = str(most_common_desc).replace('\n', ' ').replace('\r', ' ').strip()
                        if len(clean_desc) > 60:
                            clean_desc = clean_desc[:60] + "..."
                        issue_description = clean_desc
                else:
                    issue_description = "Technical Support Issue"
            else:
                issue_description = "Technical Support Issue"
            
            kb_articles_data.append({
                'kb_id': kb_id,
                'count': int(count),
                'percentage': round(percentage, 1),
                'issue_description': issue_description
            })
        
        monthly_trends = []
        for period, data in monthly_kb_trends.iterrows():
            kb_usage_rate = (data['Knowledge ID'] / data['Number'] * 100) if data['Number'] > 0 else 0
            monthly_trends.append({
                'month': str(period),
                'kb_usage_count': int(data['Knowledge ID']),
                'total_incidents': int(data['Number']),
                'kb_usage_rate': round(kb_usage_rate, 1)
            })
        
        resolution_correlation = []
        for res_type, count in resolution_type_kb.items():
            percentage = (count / kb_covered_incidents * 100) if kb_covered_incidents > 0 else 0
            resolution_correlation.append({
                'resolution_type': res_type,
                'count': int(count),
                'percentage': round(percentage, 1)
            })
        
        return jsonify({
            'status': 'success',
            'summary': {
                'total_incidents': total_incidents,
                'kb_covered_incidents': kb_covered_incidents,
                'kb_coverage_percentage': round(kb_coverage, 1),
                'unique_kb_articles': unique_kb_count
            },
            'top_kb_articles': kb_articles_data,
            'monthly_trends': monthly_trends,
            'resolution_correlation': resolution_correlation
        })
    except Exception as e:
        return jsonify({'error': f'Failed to fetch KB trending data: {str(e)}'}), 500

@app.route('/api/ai_insights')
def api_ai_insights():
    """Generate AI insights from incidents data"""
    try:
        quarter = request.args.get('quarter', 'all')
        month = request.args.get('month', 'all')
        region = request.args.get('region', 'all')
        assignment_group = request.args.get('assignment_group', 'all')
        
        filtered_df = apply_filters(incidents_df, quarter, month, region, assignment_group)
        
        # Generate comprehensive insights based on data analysis
        insights = []
        
        # Ensure we have data to analyze
        if len(filtered_df) == 0:
            insights.append({
                'category': 'Data',
                'title': 'No Data Available',
                'description': 'No incidents found for the selected filters. Try adjusting your filter criteria.',
                'severity': 'medium',
                'recommendation': 'Expand filter criteria or check data availability for the selected period.',
                'confidence': 100
            })
            return jsonify({
                'status': 'success',
                'insights_count': len(insights),
                'overall_confidence': 100,
                'insights': insights,
                'data_summary': {
                    'total_incidents': 0,
                    'analysis_period': quarter,
                    'region_filter': region,
                    'generated_at': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            })
        
        # 1. MTTR Performance Insight (Dynamic based on filtered data)
        resolved_incidents = filtered_df[filtered_df['MTTR_calculated'].notna()]
        avg_mttr_hours = resolved_incidents['MTTR_calculated'].mean() / 60 if len(resolved_incidents) > 0 else 0
        
        # Compare against SLA thresholds (4 hours baseline, 3.2 hours goal)
        if ensure_tz_aware(avg_mttr_hours) > ensure_tz_aware(4):  # Above baseline SLA
            insights.append({
                'category': 'Performance',
                'title': 'MTTR Exceeds SLA Baseline',
                'description': f'Average resolution time of {avg_mttr_hours:.1f} hours exceeds the 4-hour SLA baseline. This impacts customer satisfaction and operational targets.',
                'severity': 'high',
                'recommendation': 'Implement escalation procedures and review resource allocation for faster resolution.',
                'confidence': 95
            })
        elif ensure_tz_aware(avg_mttr_hours) > ensure_tz_aware(3.2):  # Above goal SLA but within baseline
            insights.append({
                'category': 'Performance',
                'title': 'MTTR Above Goal Target',
                'description': f'Average resolution time of {avg_mttr_hours:.1f} hours exceeds the 3.2-hour goal but meets baseline SLA. Room for improvement exists.',
                'severity': 'medium',
                'recommendation': 'Focus on process optimization and knowledge sharing to reach goal SLA.',
                'confidence': 88
            })
        elif ensure_tz_aware(avg_mttr_hours) <= ensure_tz_aware(3.2):  # Meeting goal SLA
            insights.append({
                'category': 'Performance',
                'title': 'Excellent MTTR Performance',
                'description': f'Average resolution time of {avg_mttr_hours:.1f} hours meets the 3.2-hour goal SLA. Performance is exceeding targets.',
                'severity': 'low',
                'recommendation': 'Maintain current practices and document successful processes for replication.',
                'confidence': 92
            })
        
        # 2. SLA Compliance Insight (Dynamic thresholds)
        sla_compliance = (filtered_df['sla_met_mttr'] == True).sum() / len(filtered_df) * 100 if len(filtered_df) > 0 else 0
        sla_goal_compliance = (filtered_df['sla_met_goal'] == True).sum() / len(filtered_df) * 100 if len(filtered_df) > 0 else 0
        
        if ensure_tz_aware(sla_compliance) < ensure_tz_aware(90):  # Below 90% baseline compliance
            insights.append({
                'category': 'SLA',
                'title': 'SLA Compliance Below Target',
                'description': f'Baseline SLA compliance at {sla_compliance:.1f}% is below the 95%+ target. Goal SLA compliance is {sla_goal_compliance:.1f}%.',
                'severity': 'high' if sla_compliance < 85 else 'medium',
                'recommendation': 'Review incident prioritization and implement proactive monitoring to improve SLA performance.',
                'confidence': 94
            })
        elif ensure_tz_aware(sla_goal_compliance) < ensure_tz_aware(85):  # Good baseline but poor goal compliance
            insights.append({
                'category': 'SLA',
                'title': 'Goal SLA Opportunity',
                'description': f'Baseline SLA compliance is strong at {sla_compliance:.1f}%, but goal SLA compliance at {sla_goal_compliance:.1f}% has improvement potential.',
                'severity': 'medium',
                'recommendation': 'Focus on reducing resolution time to improve goal SLA compliance rates.',
                'confidence': 86
            })
        else:  # Meeting both SLAs
            insights.append({
                'category': 'SLA',
                'title': 'Strong SLA Performance',
                'description': f'Excellent SLA performance with {sla_compliance:.1f}% baseline and {sla_goal_compliance:.1f}% goal compliance.',
                'severity': 'low',
                'recommendation': 'Continue current practices and share successful strategies across teams.',
                'confidence': 90
            })
        
        # 3. Knowledge Base Utilization Insight
        kb_coverage = (filtered_df['Knowledge ID'].notna().sum() / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
        
        if ensure_tz_aware(kb_coverage) > ensure_tz_aware(95):
            insights.append({
                'category': 'Knowledge Management',
                'title': 'Excellent KB Utilization',
                'description': f'{kb_coverage:.1f}% KB coverage indicates strong knowledge management practices. This contributes to consistent resolution quality.',
                'severity': 'low',
                'recommendation': 'Continue KB maintenance and expand coverage to emerging issue patterns.',
                'confidence': 90
            })
        elif ensure_tz_aware(kb_coverage) < ensure_tz_aware(80):
            insights.append({
                'category': 'Knowledge Management',
                'title': 'KB Coverage Gap',
                'description': f'Only {kb_coverage:.1f}% of incidents use KB articles, suggesting knowledge gaps or outdated documentation.',
                'severity': 'medium',
                'recommendation': 'Audit KB content and create articles for frequent issues without documentation.',
                'confidence': 87
            })
        
        # 4. Team Performance Analysis (Dynamic based on filtered data)
        if assignment_group and assignment_group != 'all':
            # Single team analysis
            team_data = filtered_df[filtered_df['Assignment group'] == assignment_group]
            if len(team_data) > 0:
                team_sla_compliance = (team_data['sla_met_mttr'] == True).sum() / len(team_data) * 100
                team_avg_mttr = team_data['MTTR_calculated'].mean() / 60 if len(team_data) > 0 else 0
                
                # Compare team performance to overall average
                overall_avg_mttr = filtered_df['MTTR_calculated'].mean() / 60 if len(filtered_df) > 0 else 0
                
                if team_avg_mttr > overall_avg_mttr * 1.2:  # 20% worse than average
                    insights.append({
                        'category': 'Team Performance',
                        'title': f'{assignment_group} Performance Below Average',
                        'description': f'Team MTTR of {team_avg_mttr:.1f} hours is {((team_avg_mttr/overall_avg_mttr-1)*100):.0f}% above overall average of {overall_avg_mttr:.1f} hours.',
                        'severity': 'medium',
                        'recommendation': 'Provide additional training and review complex incident handling procedures.',
                        'confidence': 87
                    })
                elif team_avg_mttr < overall_avg_mttr * 0.8:  # 20% better than average
                    insights.append({
                        'category': 'Team Performance',
                        'title': f'{assignment_group} Exceptional Performance',
                        'description': f'Team MTTR of {team_avg_mttr:.1f} hours is {((1-team_avg_mttr/overall_avg_mttr)*100):.0f}% better than overall average of {overall_avg_mttr:.1f} hours.',
                        'severity': 'low',
                        'recommendation': 'Document and share this team\'s best practices with other teams.',
                        'confidence': 90
                    })
        else:
            # Multi-team comparison
            team_mttr = filtered_df.groupby('Assignment group')['MTTR_calculated'].mean()
            if len(team_mttr) > 1:
                mttr_variance = team_mttr.std() / team_mttr.mean() * 100  # Coefficient of variation
                best_team = team_mttr.idxmin()
                worst_team = team_mttr.idxmax()
                if ensure_tz_aware(mttr_variance) > ensure_tz_aware(30):  # High variance
                    insights.append({
                        'category': 'Team Performance',
                        'title': 'Significant Performance Variance',
                        'description': f'MTTR varies by {mttr_variance:.0f}% across teams. {best_team} ({team_mttr[best_team]/60:.1f}h) vs {worst_team} ({team_mttr[worst_team]/60:.1f}h).',
                        'severity': 'medium',
                        'recommendation': 'Standardize procedures and implement knowledge transfer between high and low performing teams.',
                        'confidence': 85
                    })
        
        # 5. Workload Distribution Analysis (Dynamic)
        total_incidents = len(filtered_df)
        team_workload = filtered_df['Assignment group'].value_counts()
        
        if len(team_workload) > 1:
            max_workload = team_workload.max()
            min_workload = team_workload.min()
            workload_ratio = max_workload / min_workload if min_workload > 0 else float('inf')
            busiest_team = team_workload.idxmax()
            lightest_team = team_workload.idxmin()
            
            if ensure_tz_aware(workload_ratio) > ensure_tz_aware(2.5):  # Significant imbalance
                insights.append({
                    'category': 'Resource Management',
                    'title': 'Workload Distribution Imbalance',
                    'description': f'{busiest_team} handles {max_workload} incidents vs {lightest_team} with {min_workload} incidents ({workload_ratio:.1f}x difference).',
                    'severity': 'medium',
                    'recommendation': 'Review assignment algorithms and consider load balancing across teams.',
                    'confidence': 83
                })
        elif len(team_workload) == 1:
            # Single team handling all incidents
            single_team = team_workload.index[0]
            insights.append({
                'category': 'Resource Management',
                'title': 'Single Team Handling All Incidents',
                'description': f'{single_team} is handling all {total_incidents} incidents in the filtered dataset.',
                'severity': 'medium',
                'recommendation': 'Consider distributing workload across multiple teams to reduce single points of failure.',
                'confidence': 88
                })
        
        # 6. Trend Analysis (Dynamic based on filtered data)
        if len(filtered_df) > 0:
            # Monthly trend analysis
            monthly_incidents = filtered_df.groupby(filtered_df['Created'].dt.to_period('M'))['Number'].count()
            if len(monthly_incidents) >= 2:
                recent_trend = monthly_incidents.iloc[-1] / monthly_incidents.iloc[-2] if monthly_incidents.iloc[-2] > 0 else 1
                latest_month = monthly_incidents.index[-1]
                previous_month = monthly_incidents.index[-2]
                
                filter_context = f" in {region}" if region and region != 'all' else ""
                filter_context += f" for {assignment_group}" if assignment_group and assignment_group != 'all' else ""
                
                if ensure_tz_aware(recent_trend) > ensure_tz_aware(1.15):  # 15% increase
                    insights.append({
                        'category': 'Trend Analysis',
                        'title': 'Incident Volume Trending Up',
                        'description': f'Incident volume{filter_context} increased by {(recent_trend-1)*100:.1f}% from {previous_month} ({monthly_incidents.iloc[-2]}) to {latest_month} ({monthly_incidents.iloc[-1]}).',
                        'severity': 'medium',
                        'recommendation': 'Monitor for emerging issues and consider proactive capacity planning.',
                        'confidence': 82
                    })
                elif ensure_tz_aware(recent_trend) < ensure_tz_aware(0.85):  # 15% decrease
                    insights.append({
                        'category': 'Trend Analysis',
                        'title': 'Positive Volume Trend',
                        'description': f'Incident volume{filter_context} decreased by {(1-recent_trend)*100:.1f}% from {previous_month} ({monthly_incidents.iloc[-2]}) to {latest_month} ({monthly_incidents.iloc[-1]}).',
                        'severity': 'low',
                        'recommendation': 'Document and maintain the practices contributing to this improvement.',
                        'confidence': 85
                    })
            
            # MTTR trend analysis
            monthly_mttr = filtered_df.groupby(filtered_df['Created'].dt.to_period('M'))['MTTR_calculated'].mean()
            if len(monthly_mttr) >= 2:
                mttr_trend = monthly_mttr.iloc[-1] / monthly_mttr.iloc[-2] if monthly_mttr.iloc[-2] > 0 else 1
                latest_mttr = monthly_mttr.iloc[-1] / 60  # Convert to hours
                previous_mttr = monthly_mttr.iloc[-2] / 60  # Convert to hours
                
                if ensure_tz_aware(mttr_trend) > ensure_tz_aware(1.1):  # 10% increase in MTTR
                    insights.append({
                        'category': 'Trend Analysis',
                        'title': 'Resolution Time Increasing',
                        'description': f'Average MTTR{filter_context} increased from {previous_mttr:.1f}h to {latest_mttr:.1f}h ({(mttr_trend-1)*100:.1f}% increase).',
                        'severity': 'medium',
                        'recommendation': 'Investigate causes of longer resolution times and address process bottlenecks.',
                        'confidence': 87
                    })
                elif ensure_tz_aware(mttr_trend) < ensure_tz_aware(0.9):  # 10% decrease in MTTR
                    insights.append({
                        'category': 'Trend Analysis',
                        'title': 'Resolution Time Improving',
                        'description': f'Average MTTR{filter_context} improved from {previous_mttr:.1f}h to {latest_mttr:.1f}h ({(1-mttr_trend)*100:.1f}% improvement).',
                        'severity': 'low',
                        'recommendation': 'Continue and expand the practices that are driving this improvement.',
                        'confidence': 89
                    })
        
        # Sort insights by severity and confidence
        severity_order = {'high': 3, 'medium': 2, 'low': 1}
        insights.sort(key=lambda x: (severity_order[x['severity']], x['confidence']), reverse=True)
        
        # Limit to top 8 insights for dashboard display
        insights = insights[:8]
        
        # Calculate overall confidence score
        overall_confidence = sum(insight['confidence'] for insight in insights) / len(insights) if insights else 0
        
        return jsonify({
            'status': 'success',
            'insights_count': len(insights),
            'overall_confidence': round(overall_confidence, 0),
            'insights': insights,
            'data_summary': {
                'total_incidents': total_incidents,
                'analysis_period': quarter,
                'region_filter': region,
                'generated_at': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except Exception as e:
        return jsonify({'error': f'Failed to generate AI insights: {str(e)}'}), 500

@app.route('/consultations')
def consultations_dashboard():
    """Serve the consultations dashboard page"""
    return render_template('consultations.html')



# Helper function for consultation filtering
def apply_consultation_filters(df, quarter=None, location=None, region=None, month=None):
    """Apply filters to consultation dataframe using consistent date ranges"""
    filtered_df = df.copy()
    
    # Apply month filter (takes precedence over quarter)
    if month and month != 'all':
        try:
            # Try to handle various month formats
            # First check if it's in YYYY-MM format
            if '-' in month and len(month.split('-')) == 2:
                year, month_num = month.split('-')
                try:
                    # Validate year and month
                    year = int(year)
                    month_num = int(month_num)
                    
                    # Create proper date range for the entire month
                    start_date = pd.Timestamp(f"{year}-{month_num:02d}-01", tz='UTC')
                    
                    # Calculate end of month correctly
                    if ensure_tz_aware(month_num) == ensure_tz_aware(12):
                        end_date = pd.Timestamp(f"{year+1}-01-01", tz='UTC') - pd.Timedelta(seconds=1)
                    else:
                        end_date = pd.Timestamp(f"{year}-{month_num+1:02d}-01", tz='UTC') - pd.Timedelta(seconds=1)
                except (ValueError, TypeError):
                    # If parsing fails, try standardize_date
                    parsed_date = standardize_date(month + "-01")
                    if parsed_date is not None:
                        # Get year and month from parsed date
                        year = parsed_date.year
                        month_num = parsed_date.month
                        
                        # Create proper date range
                        start_date = pd.Timestamp(f"{year}-{month_num:02d}-01", tz='UTC')
                        if ensure_tz_aware(month_num) == ensure_tz_aware(12):
                            end_date = pd.Timestamp(f"{year+1}-01-01", tz='UTC') - pd.Timedelta(seconds=1)
                        else:
                            end_date = pd.Timestamp(f"{year}-{month_num+1:02d}-01", tz='UTC') - pd.Timedelta(seconds=1)
                    else:
                        raise ValueError(f"Could not parse month: {month}")
            else:
                # Try to parse as a date string like "January 2025" or "Jan 2025"
                parsed_date = standardize_date(f"01 {month}")
                if parsed_date is None:
                    parsed_date = standardize_date(month + " 01")
                
                if parsed_date is not None:
                    year = parsed_date.year
                    month_num = parsed_date.month
                    
                    # Create proper date range
                    start_date = pd.Timestamp(f"{year}-{month_num:02d}-01", tz='UTC')
                    if ensure_tz_aware(month_num) == ensure_tz_aware(12):
                        end_date = pd.Timestamp(f"{year+1}-01-01", tz='UTC') - pd.Timedelta(seconds=1)
                    else:
                        end_date = pd.Timestamp(f"{year}-{month_num+1:02d}-01", tz='UTC') - pd.Timedelta(seconds=1)
                else:
                    print(f"Could not parse month format: {month}")
                    return filtered_df
            
            # Apply the date range filter
            filtered_df = filtered_df[
                (filtered_df['Created'] >= start_date) & 
                (filtered_df['Created'] <= end_date)
            ]
        except Exception as e:
            # Handle any errors in month parsing
            print(f"Error processing month filter: {month}, error: {e}")
            pass
    elif quarter and quarter != 'all':
        # Use the same date range function for consistency
        start_date, end_date = get_date_range_for_quarter(quarter)
        filtered_df = filtered_df[
            (filtered_df['Created'] >= start_date) & 
            (filtered_df['Created'] <= end_date)
        ]
    
    # Apply location filter
    if location and location != 'all':
        filtered_df = filtered_df[filtered_df['Location'] == location]
    
    # Apply region filter
    if region and region != 'all':
        filtered_df = filtered_df[filtered_df['Region'] == region]
    
    return filtered_df


def generate_type_specific_metrics(type_df, consultation_type):
    """Generate metrics specific to each consultation type"""
    metrics = {}
    
    if consultation_type == 'INC Created':
        # For INC Created: Focus on incident validation and creation effectiveness
        inc_numbers = type_df['INC %23'].dropna()
        
        # Check for valid INC number format (starts with INC and has digits)
        valid_format = int(inc_numbers.str.match(r'^INC\d+', na=False).sum())
        invalid_format = len(inc_numbers) - valid_format
        
        # Cross-reference with actual incident data if available
        if incidents_df is not None:
            valid_incidents = inc_numbers[inc_numbers.isin(incidents_df['Number'])]
            metrics['valid_incidents'] = int(len(valid_incidents))
            metrics['invalid_incidents'] = int(len(inc_numbers) - len(valid_incidents))
            metrics['incident_validation_rate'] = float((len(valid_incidents) / len(inc_numbers)) * 100) if len(inc_numbers) > 0 else 0.0
        else:
            metrics['valid_incidents'] = int(valid_format)
            metrics['invalid_incidents'] = int(invalid_format)
            metrics['incident_validation_rate'] = float((valid_format / len(inc_numbers)) * 100) if len(inc_numbers) > 0 else 0.0
        
        metrics['total_inc_numbers'] = int(len(inc_numbers))
        metrics['missing_inc_count'] = int(len(type_df) - len(inc_numbers))
        
    elif ensure_tz_aware(consultation_type) == ensure_tz_aware('Equipment'):
        # For Equipment: Focus on equipment types and fulfillment
        equipment_types = type_df['Equipment Type'].value_counts()
        metrics['unique_equipment_types'] = int(len(equipment_types))
        metrics['top_equipment_type'] = equipment_types.index[0] if len(equipment_types) > 0 else 'N/A'
        metrics['top_equipment_count'] = int(equipment_types.iloc[0]) if len(equipment_types) > 0 else 0
        metrics['equipment_with_inc'] = int(type_df['INC %23'].notna().sum())
        metrics['equipment_fulfillment_rate'] = float(((len(type_df) - type_df['INC %23'].notna().sum()) / len(type_df)) * 100) if len(type_df) > 0 else 0.0
        
    elif consultation_type == 'Customer Education':
        # For Customer Education: Focus on education effectiveness
        with_inc = int(type_df['INC %23'].notna().sum())
        without_inc = len(type_df) - with_inc
        metrics['education_success_rate'] = float((without_inc / len(type_df)) * 100) if len(type_df) > 0 else 0.0
        metrics['escalated_to_inc'] = int(with_inc)
        metrics['resolved_through_education'] = int(without_inc)
        
        # Analyze common issues for education
        issue_patterns = type_df['Issue'].value_counts()
        metrics['top_education_topic'] = issue_patterns.index[0] if len(issue_patterns) > 0 else 'N/A'
        metrics['top_topic_count'] = int(issue_patterns.iloc[0]) if len(issue_patterns) > 0 else 0
        
    elif consultation_type == 'General Inquiry':
        # For General Inquiry: Focus on inquiry resolution
        with_inc = int(type_df['INC %23'].notna().sum())
        metrics['inquiry_escalation_rate'] = float((with_inc / len(type_df)) * 100) if len(type_df) > 0 else 0.0
        metrics['direct_resolution'] = int(len(type_df) - with_inc)
        metrics['escalated_inquiries'] = int(with_inc)
        
        # Common inquiry types
        issue_types = type_df['Issue'].value_counts()
        metrics['top_inquiry_type'] = issue_types.index[0] if len(issue_types) > 0 else 'N/A'
        metrics['top_inquiry_count'] = int(issue_types.iloc[0]) if len(issue_types) > 0 else 0
        
    elif consultation_type == 'Cancel this Consultation':
        # For Cancellations: Focus on cancellation patterns
        metrics['total_cancellations'] = int(len(type_df))
        metrics['cancellations_with_inc'] = int(type_df['INC %23'].notna().sum())
        
        # Analyze cancellation timing (time between created and modified)
        time_diff = (type_df['Modified'] - type_df['Created']).dt.total_seconds() / 60  # minutes
        metrics['avg_cancellation_time'] = float(time_diff.mean()) if len(time_diff) > 0 else 0
        metrics['quick_cancellations'] = int((time_diff < 15).sum()) if len(time_diff) > 0 else 0  # < 15 minutes
        
    elif consultation_type == 'Customer Abandon':
        # For Abandonment: Focus on abandonment patterns
        metrics['total_abandons'] = int(len(type_df))
        metrics['abandons_with_inc'] = int(type_df['INC %23'].notna().sum())
        
        # Analyze abandonment timing
        time_diff = (type_df['Modified'] - type_df['Created']).dt.total_seconds() / 60  # minutes
        metrics['avg_abandon_time'] = float(time_diff.mean()) if len(time_diff) > 0 else 0
        metrics['immediate_abandons'] = int((time_diff < 5).sum()) if len(time_diff) > 0 else 0  # < 5 minutes
        
        # Day of week analysis
        abandon_days = type_df['Created'].dt.day_name().value_counts()
        metrics['peak_abandon_day'] = abandon_days.index[0] if len(abandon_days) > 0 else 'N/A'
        metrics['peak_day_count'] = int(abandon_days.iloc[0]) if len(abandon_days) > 0 else 0
    
    return metrics


def generate_type_specific_insights(consultation_type, metrics, technicians, locations, inc_creation_rate, inc_created, total_consultations):
    """Generate insights specific to each consultation type"""
    insights = []
    
    if consultation_type == 'INC Created':
        # Incident validation insights
        if 'incident_validation_rate' in metrics:
            validation_rate = metrics['incident_validation_rate']
            if ensure_tz_aware(validation_rate) < ensure_tz_aware(80):
                insights.append({
                    'type': 'quality',
                    'title': 'INC Number Validation Issue',
                    'description': f"Only {validation_rate:.1f}% of INC numbers are valid/exist in incident data. {metrics['invalid_incidents']} invalid INC numbers found.",
                    'metric': f"{metrics['valid_incidents']} valid / {metrics['total_inc_numbers']} total"
                })
            else:
                insights.append({
                    'type': 'quality',
                    'title': 'High INC Quality',
                    'description': f"Excellent INC number quality with {validation_rate:.1f}% valid incident numbers.",
                    'metric': f"{metrics['valid_incidents']} validated incidents"
                })
        
        if ensure_tz_aware(metrics['missing_inc_count']) > ensure_tz_aware(0):
            missing_rate = (metrics['missing_inc_count'] / total_consultations) * 100
            insights.append({
                'type': 'process',
                'title': 'Missing INC Documentation',
                'description': f"{metrics['missing_inc_count']} consultations ({missing_rate:.1f}%) marked as 'INC Created' but missing incident numbers.",
                'metric': f"{missing_rate:.1f}% documentation gap"
            })
    
    elif ensure_tz_aware(consultation_type) == ensure_tz_aware('Equipment'):
        # Equipment fulfillment insights
        fulfillment_rate = metrics.get('equipment_fulfillment_rate', 0)
        if ensure_tz_aware(fulfillment_rate) > ensure_tz_aware(85):
            insights.append({
                'type': 'performance',
                'title': 'High Equipment Fulfillment',
                'description': f"Equipment requests have {fulfillment_rate:.1f}% direct fulfillment rate without escalation to incidents.",
                'metric': f"{fulfillment_rate:.1f}% success rate"
            })
        
        if metrics.get('unique_equipment_types', 0) > 0:
            insights.append({
                'type': 'pattern',
                'title': f"Top Equipment Request: {metrics['top_equipment_type']}",
                'description': f"{metrics['top_equipment_type']} is the most requested equipment type with {metrics['top_equipment_count']} requests.",
                'metric': f"{metrics['top_equipment_count']} requests"
            })
    
    elif consultation_type == 'Customer Education':
        # Education effectiveness insights
        success_rate = metrics.get('education_success_rate', 0)
        if ensure_tz_aware(success_rate) > ensure_tz_aware(90):
            insights.append({
                'type': 'performance',
                'title': 'Highly Effective Education',
                'description': f"Customer education is {success_rate:.1f}% effective - most issues resolved without escalation.",
                'metric': f"{metrics['resolved_through_education']} resolved directly"
            })
        
        if 'top_education_topic' in metrics and metrics['top_education_topic'] != 'N/A':
            insights.append({
                'type': 'pattern',
                'title': f"Primary Education Topic",
                'description': f"'{metrics['top_education_topic']}' is the most common education topic with {metrics['top_topic_count']} consultations.",
                'metric': f"{metrics['top_topic_count']} consultations"
            })
    
    elif consultation_type == 'General Inquiry':
        # Inquiry resolution insights
        escalation_rate = metrics.get('inquiry_escalation_rate', 0)
        if ensure_tz_aware(escalation_rate) < ensure_tz_aware(5):
            insights.append({
                'type': 'performance',
                'title': 'Excellent Inquiry Resolution',
                'description': f"Only {escalation_rate:.1f}% of general inquiries require escalation to incidents.",
                'metric': f"{metrics['direct_resolution']} resolved directly"
            })
        
        if 'top_inquiry_type' in metrics and metrics['top_inquiry_type'] != 'N/A':
            insights.append({
                'type': 'pattern',
                'title': 'Most Common Inquiry',
                'description': f"'{metrics['top_inquiry_type']}' represents the most frequent inquiry type.",
                'metric': f"{metrics['top_inquiry_count']} inquiries"
            })
    
    elif consultation_type == 'Cancel this Consultation':
        # Cancellation pattern insights
        if 'avg_cancellation_time' in metrics:
            avg_time = metrics['avg_cancellation_time']
            if ensure_tz_aware(avg_time) < ensure_tz_aware(30):
                insights.append({
                    'type': 'pattern',
                    'title': 'Quick Cancellation Pattern',
                    'description': f"Consultations are cancelled quickly (avg {avg_time:.1f} minutes), suggesting scheduling issues or immediate resolution.",
                    'metric': f"{metrics['quick_cancellations']} quick cancels"
                })
        
        if metrics.get('cancellations_with_inc', 0) > 0:
            insights.append({
                'type': 'process',
                'title': 'Cancelled with INC Created',
                'description': f"{metrics['cancellations_with_inc']} cancelled consultations still created incident tickets.",
                'metric': f"{metrics['cancellations_with_inc']} INC tickets"
            })
    
    elif consultation_type == 'Customer Abandon':
        # Abandonment pattern insights
        if 'avg_abandon_time' in metrics:
            avg_time = metrics['avg_abandon_time']
            if ensure_tz_aware(avg_time) < ensure_tz_aware(10):
                insights.append({
                    'type': 'pattern',
                    'title': 'Immediate Abandonment Pattern',
                    'description': f"Customers abandon quickly (avg {avg_time:.1f} minutes), suggesting wait time or accessibility issues.",
                    'metric': f"{metrics['immediate_abandons']} immediate abandons"
                })
        
        if 'peak_abandon_day' in metrics and metrics['peak_abandon_day'] != 'N/A':
            insights.append({
                'type': 'timing',
                'title': f"Peak Abandonment: {metrics['peak_abandon_day']}",
                'description': f"{metrics['peak_abandon_day']} has the highest abandonment rate with {metrics['peak_day_count']} abandoned consultations.",
                'metric': f"{metrics['peak_day_count']} abandons"
            })
    
    # Add top performer insight for all types
    if len(technicians) > 0:
        top_tech = technicians[0]
        insights.append({
            'type': 'performance',
            'title': 'Top Performer',
            'description': f"{top_tech['technician_name']} handles {top_tech['percentage_of_type']}% of all {consultation_type} consultations.",
            'metric': f"{top_tech['total_consultations']} consultations"
        })
    
    return insights

@app.route('/api/consultations/locations')
def api_consultations_locations():
    """Get available consultation locations with statistics"""
    if consultations_df is None:
        return jsonify({'error': 'Consultation data not loaded'}), 500
    
    try:
        # Get filter parameters
        region = request.args.get('region', 'all')
        
        # Filter by region if specified
        if region != 'all':
            filtered_df = consultations_df[consultations_df['Region'] == region]
        else:
            filtered_df = consultations_df
        
        # Get all unique locations with their consultation counts
        location_stats = filtered_df.groupby('Location').agg({
            'ID': 'count',
            'Consult Complete': lambda x: (x == 'Yes').sum()
        }).rename(columns={'ID': 'consultation_count', 'Consult Complete': 'completed_count'})
        
        # Calculate completion rates
        location_stats['completion_rate'] = (location_stats['completed_count'] / location_stats['consultation_count']) * 100
        
        # Sort by consultation count (descending)
        location_stats = location_stats.sort_values('consultation_count', ascending=False)
        
        # Prepare response data
        locations = []
        total_consultations = len(filtered_df)
        
        for location, stats in location_stats.iterrows():
            percentage = (stats['consultation_count'] / total_consultations) * 100
            # Get the region for this location
            location_region = 'Unknown'
            location_data = filtered_df[filtered_df['Location'] == location]
            if len(location_data) > 0:
                location_region = location_data['Region'].iloc[0]
                
            locations.append({
                'value': location,
                'display_name': location,
                'consultation_count': int(stats['consultation_count']),
                'completed_count': int(stats['completed_count']),
                'completion_rate': round(stats['completion_rate'], 1),
                'percentage': round(percentage, 1),
                'region': location_region
            })
        
        return jsonify({
            'status': 'success',
            'locations': locations,
            'total_locations': len(locations),
            'total_consultations': total_consultations,
            'filtered_by_region': region != 'all',
            'region': region
        })
    except Exception as e:
        return jsonify({'error': f'Failed to get consultation locations: {str(e)}'}), 500

@app.route('/api/consultations/regions')
def api_consultations_regions():
    """Get available consultation regions with statistics"""
    if consultations_df is None:
        return jsonify({'error': 'Consultation data not loaded'}), 500
    
    try:
        # Get all unique regions with their consultation counts
        region_stats = consultations_df.groupby('Region').agg({
            'ID': 'count',
            'Consult Complete': lambda x: (x == 'Yes').sum()
        }).rename(columns={'ID': 'consultation_count', 'Consult Complete': 'completed_count'})
        
        # Calculate completion rates
        region_stats['completion_rate'] = (region_stats['completed_count'] / region_stats['consultation_count']) * 100
        
        # Sort by consultation count (descending)
        region_stats = region_stats.sort_values('consultation_count', ascending=False)
        
        # Prepare response data
        regions = []
        total_consultations = len(consultations_df)
        
        for region, stats in region_stats.iterrows():
            percentage = (stats['consultation_count'] / total_consultations) * 100
            regions.append({
                'value': region,
                'display_name': region,
                'consultation_count': int(stats['consultation_count']),
                'completed_count': int(stats['completed_count']),
                'completion_rate': round(stats['completion_rate'], 1),
                'percentage': round(percentage, 1)
            })
        
        return jsonify({
            'status': 'success',
            'regions': regions,
            'total_regions': len(regions),
            'total_consultations': total_consultations
        })
    except Exception as e:
        return jsonify({'error': f'Failed to get consultation regions: {str(e)}'}), 500

@app.route('/api/consultations/overview')
def api_consultations_overview():
    """Get consultation overview metrics with location and region filtering"""
    if consultations_df is None:
        return jsonify({'error': 'Consultation data not loaded'}), 500
    
    quarter = request.args.get('quarter', 'all')
    month = request.args.get('month', 'all')
    location = request.args.get('location', 'all')
    region = request.args.get('region', 'all')
    
    filtered_df = apply_consultation_filters(consultations_df, quarter, location, region, month)
    
    # Calculate key metrics
    total_consultations = len(filtered_df)
    completed_consultations = (filtered_df['Consult Complete'] == 'Yes').sum()
    completion_rate = (completed_consultations / total_consultations) * 100 if total_consultations > 0 else 0
    
    # Get breakdown by Consultation Defined (type)
    completed_df = filtered_df[filtered_df['Consult Complete'] == 'Yes']
    consultation_types = completed_df['Consultation Defined'].value_counts().to_dict()
    
    # Calculate percentages for each type
    consultation_type_breakdown = {}
    for cons_type, count in consultation_types.items():
        consultation_type_breakdown[cons_type] = {
            'count': int(count),
            'percentage': round((count / completed_consultations) * 100, 1) if completed_consultations > 0 else 0
        }
    
    # INC creation rate (consultations that resulted in incidents)
    inc_created = filtered_df['INC %23'].notna().sum()
    inc_creation_rate = (inc_created / total_consultations) * 100 if total_consultations > 0 else 0
    
    # Data quality metrics: Completed consultations without INC numbers
    completed_without_inc = completed_df[completed_df['INC %23'].isna()]
    missing_inc_count = len(completed_without_inc)
    missing_inc_rate = (missing_inc_count / completed_consultations) * 100 if completed_consultations > 0 else 0
    
    # Specific analysis for "Tech Support" consultations without INC numbers
    tech_support_completed = completed_df[completed_df['Issue'] == 'I need Tech Support']
    tech_support_without_inc = tech_support_completed[tech_support_completed['INC %23'].isna()]
    tech_support_missing_inc = len(tech_support_without_inc)
    
    # Unique locations and technicians
    unique_locations = filtered_df['Location'].nunique()
    unique_technicians = filtered_df['Technician Name'].nunique()
    
    return jsonify({
        'total_consultations': int(total_consultations),
        'completed_consultations': int(completed_consultations),
        'completion_rate': round(completion_rate, 1),
        'consultation_type_breakdown': consultation_type_breakdown,
        'inc_created': int(inc_created),
        'inc_creation_rate': round(inc_creation_rate, 1),
        'missing_inc_count': int(missing_inc_count),
        'missing_inc_rate': round(missing_inc_rate, 1),
        'tech_support_missing_inc': int(tech_support_missing_inc),
        'unique_locations': int(unique_locations),
        'unique_technicians': int(unique_technicians),
        'quarter': quarter,
        'location': location,
        'region': region
    })

@app.route('/api/consultations/trends')
def api_consultations_trends():
    """Get consultation trends data for charts with location and region filtering"""
    if consultations_df is None:
        return jsonify({'error': 'Consultation data not loaded'}), 500
    
    quarter = request.args.get('quarter', 'all')
    month = request.args.get('month', 'all')
    location = request.args.get('location', 'all')
    region = request.args.get('region', 'all')
    
    filtered_df = apply_consultation_filters(consultations_df, quarter, location, region, month)
    
    # Monthly consultation trends
    monthly_data = filtered_df.groupby(filtered_df['Created'].dt.to_period('M')).agg({
        'ID': 'count',
        'Consult Complete': lambda x: (x == 'Yes').sum(),
        'INC %23': lambda x: x.notna().sum()
    }).round(0)
    
    monthly_data = monthly_data.sort_index()
    
    # Prepare chart data
    consultation_data = []
    completion_data = []
    
    for period, row in monthly_data.iterrows():
        month_name = period.strftime('%b %Y')
        
        consultation_data.append({
            'month': month_name,
            'value': int(row['ID'])
        })
        
        completion_data.append({
            'month': month_name,
            'value': int(row['Consult Complete'])
        })
    
    return jsonify({
        'consultation_trends': {
            'data': consultation_data
        },
        'completion_trends': {
            'data': completion_data
        },
        'quarter': quarter,
        'location': location,
        'region': region
    })

@app.route('/api/consultations/issue-breakdown')
def api_consultations_issue_breakdown():
    """Get consultation issue breakdown for pie chart with location and region filtering"""
    if consultations_df is None:
        return jsonify({'error': 'Consultation data not loaded'}), 500
    
    quarter = request.args.get('quarter', 'all')
    month = request.args.get('month', 'all')
    location = request.args.get('location', 'all')
    region = request.args.get('region', 'all')
    
    filtered_df = apply_consultation_filters(consultations_df, quarter, location, region, month)
    
    # Get issue breakdown (top 8 issues + others)
    issue_counts = filtered_df['Issue'].value_counts()
    top_issues = issue_counts.head(8)
    others_count = issue_counts.iloc[8:].sum() if len(issue_counts) > 8 else 0
    
    # Prepare data for pie chart
    labels = top_issues.index.tolist()
    data = [int(count) for count in top_issues.values]
    
    if ensure_tz_aware(others_count) > ensure_tz_aware(0):
        labels.append('Others')
        data.append(int(others_count))
    
    return jsonify({
        'labels': labels,
        'data': data,
        'total': int(len(filtered_df)),
        'quarter': quarter,
        'location': location,
        'region': region
    })

@app.route('/api/consultations/technician-drilldown')
def api_consultations_technician_drilldown():
    """Get detailed technician breakdown for drill-down modals"""
    if consultations_df is None:
        return jsonify({'error': 'Consultation data not loaded'}), 500
    
    quarter = request.args.get('quarter', 'all')
    month = request.args.get('month', 'all')
    location = request.args.get('location', 'all')
    region = request.args.get('region', 'all')
    issue = request.args.get('issue')  # Optional: filter by specific issue type
    
    filtered_df = apply_consultation_filters(consultations_df, quarter, location, region, month)
    
    # Additional issue filter if specified
    if issue and issue != 'all' and issue != 'Others':
        filtered_df = filtered_df[filtered_df['Issue'] == issue]
    elif ensure_tz_aware(issue) == ensure_tz_aware('Others'):
        # For "Others" category, exclude top 8 issues
        top_8_issues = consultations_df['Issue'].value_counts().head(8).index.tolist()
        filtered_df = filtered_df[~filtered_df['Issue'].isin(top_8_issues)]
    
    # Calculate technician metrics
    technician_stats = filtered_df.groupby('Technician Name').agg({
        'ID': 'count',
        'Consult Complete': lambda x: (x == 'Yes').sum(),
        'INC %23': lambda x: x.notna().sum(),
        'Issue': lambda x: x.value_counts().index[0] if len(x) > 0 else 'N/A'  # Most common issue
    }).rename(columns={
        'ID': 'total_consultations',
        'Consult Complete': 'completed_consultations',
        'INC %23': 'inc_created',
        'Issue': 'top_issue'
    })
    
    # Calculate rates
    technician_stats['completion_rate'] = (technician_stats['completed_consultations'] / technician_stats['total_consultations']) * 100
    technician_stats['inc_creation_rate'] = (technician_stats['inc_created'] / technician_stats['total_consultations']) * 100
    
    # Sort by total consultations (descending)
    technician_stats = technician_stats.sort_values('total_consultations', ascending=False)
    
    # Prepare response data
    technicians = []
    for tech_name, stats in technician_stats.iterrows():
        technicians.append({
            'technician_name': tech_name,
            'total_consultations': int(stats['total_consultations']),
            'completed_consultations': int(stats['completed_consultations']),
            'completion_rate': round(stats['completion_rate'], 1),
            'inc_created': int(stats['inc_created']),
            'inc_creation_rate': round(stats['inc_creation_rate'], 1),
            'top_issue': stats['top_issue']
        })
    
    return jsonify({
        'status': 'success',
        'technicians': technicians,
        'total_technicians': len(technicians),
        'filters': {
            'quarter': quarter,
            'location': location,
            'issue': issue
        },
        'summary': {
            'total_consultations': int(filtered_df.shape[0]),
            'avg_completion_rate': round(technician_stats['completion_rate'].mean(), 1),
            'avg_inc_rate': round(technician_stats['inc_creation_rate'].mean(), 1)
        }
    })

@app.route('/api/consultations/location-drilldown')
def api_consultations_location_drilldown():
    """Get detailed location breakdown with technician details"""
    if consultations_df is None:
        return jsonify({'error': 'Consultation data not loaded'}), 500
    
    quarter = request.args.get('quarter', 'all')
    month = request.args.get('month', 'all')
    target_location = request.args.get('target_location')  # Specific location to drill down into
    region = request.args.get('region', 'all')
    
    # Apply quarter, month and region filters
    filtered_df = apply_consultation_filters(consultations_df, quarter, 'all', region, month)
    
    if target_location and target_location != 'all':
        # Drill down into specific location
        location_df = filtered_df[filtered_df['Location'] == target_location]
        
        # Get technician breakdown for this location
        tech_stats = location_df.groupby('Technician Name').agg({
            'ID': 'count',
            'Consult Complete': lambda x: (x == 'Yes').sum(),
            'INC %23': lambda x: x.notna().sum()
        }).rename(columns={
            'ID': 'total_consultations',
            'Consult Complete': 'completed_consultations',
            'INC %23': 'inc_created'
        })
        
        tech_stats['completion_rate'] = (tech_stats['completed_consultations'] / tech_stats['total_consultations']) * 100
        tech_stats['inc_creation_rate'] = (tech_stats['inc_created'] / tech_stats['total_consultations']) * 100
        tech_stats = tech_stats.sort_values('total_consultations', ascending=False)
        
        technicians = []
        for tech_name, stats in tech_stats.iterrows():
            technicians.append({
                'technician_name': tech_name,
                'total_consultations': int(stats['total_consultations']),
                'completed_consultations': int(stats['completed_consultations']),
                'completion_rate': round(stats['completion_rate'], 1),
                'inc_created': int(stats['inc_created']),
                'inc_creation_rate': round(stats['inc_creation_rate'], 1)
            })
        
        return jsonify({
            'status': 'success',
            'location': target_location,
            'technicians': technicians,
            'total_technicians': len(technicians),
            'quarter': quarter,
            'region': region,
            'summary': {
                'total_consultations': int(len(location_df)),
                'completed_consultations': int((location_df['Consult Complete'] == 'Yes').sum()),
                'completion_rate': round(((location_df['Consult Complete'] == 'Yes').sum() / len(location_df)) * 100, 1)
            }
        })
    else:
        # Get all locations summary
        location_stats = filtered_df.groupby('Location').agg({
            'ID': 'count',
            'Consult Complete': lambda x: (x == 'Yes').sum(),
            'INC %23': lambda x: x.notna().sum(),
            'Technician Name': 'nunique'
        }).rename(columns={
            'ID': 'total_consultations',
            'Consult Complete': 'completed_consultations',
            'INC %23': 'inc_created',
            'Technician Name': 'unique_technicians'
        })
        
        location_stats['completion_rate'] = (location_stats['completed_consultations'] / location_stats['total_consultations']) * 100
        location_stats['inc_creation_rate'] = (location_stats['inc_created'] / location_stats['total_consultations']) * 100
        location_stats = location_stats.sort_values('total_consultations', ascending=False)
        
        locations = []
        for location_name, stats in location_stats.iterrows():
            locations.append({
                'location': location_name,
                'total_consultations': int(stats['total_consultations']),
                'completed_consultations': int(stats['completed_consultations']),
                'completion_rate': round(stats['completion_rate'], 1),
                'inc_created': int(stats['inc_created']),
                'inc_creation_rate': round(stats['inc_creation_rate'], 1),
                'unique_technicians': int(stats['unique_technicians'])
            })
        
        return jsonify({
            'status': 'success',
            'locations': locations,
            'total_locations': len(locations),
            'quarter': quarter,
            'region': region
        })

@app.route('/api/consultations/month-drilldown')
def api_consultations_month_drilldown():
    """Get detailed monthly breakdown for consultation volume drill-down"""
    if consultations_df is None:
        return jsonify({'error': 'Consultation data not loaded'}), 500
    
    month = request.args.get('month')
    location = request.args.get('location', 'all')
    region = request.args.get('region', 'all')
    
    if not month or month == 'all':
        # Use current month as default
        current_date = datetime.now()
        month = f"{current_date.year}-{current_date.month:02d}"
        print(f"Month parameter not provided, using current month: {month}")
        return jsonify({'error': 'Month parameter is required'}), 400
    
    # For month drilldown, we use the month parameter directly
    filtered_df = apply_consultation_filters(consultations_df, 'all', location, region, month)
    
    target_month = month
    
    if target_month and target_month != 'all':
        # Parse target month
        try:
            month_period = pd.Period(target_month, freq='M')
            month_df = filtered_df[filtered_df['Created'].dt.to_period('M') == month_period]
            
            # Daily breakdown for the specific month
            daily_stats = month_df.groupby(month_df['Created'].dt.date).agg({
                'ID': 'count',
                'Consult Complete': lambda x: (x == 'Yes').sum(),
                'INC %23': lambda x: x.notna().sum()
            }).rename(columns={
                'ID': 'total_consultations',
                'Consult Complete': 'completed_consultations',
                'INC %23': 'inc_created'
            })
            
            daily_data = []
            for date, stats in daily_stats.iterrows():
                completion_rate = (stats['completed_consultations'] / stats['total_consultations']) * 100 if stats['total_consultations'] > 0 else 0
                daily_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'day_name': date.strftime('%A'),
                    'total_consultations': int(stats['total_consultations']),
                    'completed_consultations': int(stats['completed_consultations']),
                    'completion_rate': round(completion_rate, 1),
                    'inc_created': int(stats['inc_created'])
                })
            
            # Sort by date
            daily_data = sorted(daily_data, key=lambda x: x['date'])
            
            # Top technicians for this month
            tech_stats = month_df.groupby('Technician Name').agg({
                'ID': 'count',
                'Consult Complete': lambda x: (x == 'Yes').sum()
            }).rename(columns={'ID': 'total_consultations', 'Consult Complete': 'completed_consultations'})
            
            tech_stats['completion_rate'] = (tech_stats['completed_consultations'] / tech_stats['total_consultations']) * 100
            tech_stats = tech_stats.sort_values('total_consultations', ascending=False).head(10)
            
            top_technicians = []
            for tech_name, stats in tech_stats.iterrows():
                top_technicians.append({
                    'technician_name': tech_name,
                    'total_consultations': int(stats['total_consultations']),
                    'completed_consultations': int(stats['completed_consultations']),
                    'completion_rate': round(stats['completion_rate'], 1)
                })
            
            return jsonify({
                'status': 'success',
                'month': target_month,
                'daily_breakdown': daily_data,
                'top_technicians': top_technicians,
                'filters': {
                    'location': location,
                    'region': region
                },
                'summary': {
                    'total_consultations': int(len(month_df)),
                    'total_days': len(daily_data),
                    'avg_daily_consultations': round(len(month_df) / len(daily_data), 1) if daily_data else 0
                }
            })
        except Exception as e:
            return jsonify({'error': f'Invalid month format: {str(e)}'}), 400
    else:
        # Return monthly summary
        monthly_stats = filtered_df.groupby(filtered_df['Created'].dt.to_period('M')).agg({
            'ID': 'count',
            'Consult Complete': lambda x: (x == 'Yes').sum(),
            'INC %23': lambda x: x.notna().sum(),
            'Technician Name': 'nunique'
        }).rename(columns={
            'ID': 'total_consultations',
            'Consult Complete': 'completed_consultations',
            'INC %23': 'inc_created',
            'Technician Name': 'unique_technicians'
        })
        
        monthly_data = []
        for period, stats in monthly_stats.iterrows():
            completion_rate = (stats['completed_consultations'] / stats['total_consultations']) * 100 if stats['total_consultations'] > 0 else 0
            monthly_data.append({
                'month': period.strftime('%b %Y'),
                'total_consultations': int(stats['total_consultations']),
                'completed_consultations': int(stats['completed_consultations']),
                'completion_rate': round(completion_rate, 1),
                'inc_created': int(stats['inc_created']),
                'unique_technicians': int(stats['unique_technicians'])
            })
        
        return jsonify({
            'status': 'success',
            'monthly_breakdown': monthly_data,
            'filters': {
                'location': location
            }
        })

@app.route('/api/consultations/ai-insights')
def api_consultations_ai_insights():
    """Get AI-generated insights from consultation data with location and region filtering"""
    if consultations_df is None:
        return jsonify({'error': 'Consultation data not loaded'}), 500
    
    quarter = request.args.get('quarter', 'all')
    month = request.args.get('month', 'all')
    location = request.args.get('location', 'all')
    region = request.args.get('region', 'all')
    
    filtered_df = apply_consultation_filters(consultations_df, quarter, location, region, month)
    
    # Generate AI insights based on filtered data analysis
    insights = []
    
    # 1. Volume Analysis
    total_consultations = len(filtered_df)
    if quarter == 'all' and total_consultations > 0:
        monthly_counts = filtered_df.groupby(filtered_df['Created'].dt.month).size()
        if len(monthly_counts) > 1:
            peak_month = monthly_counts.idxmax()
            peak_count = monthly_counts.max()
            low_month = monthly_counts.idxmin()
            low_count = monthly_counts.min()
            
            month_names = {2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June'}
            
            insights.append({
                'type': 'volume',
                'title': 'Peak Demand Analysis',
                'description': f'{month_names[peak_month]} had the highest consultation volume with {peak_count:,} requests, while {month_names[low_month]} had the lowest with {low_count:,}.',
                'impact': 'high',
                'metric': f'{((peak_count - low_count) / low_count * 100):.1f}% variance'
            })
    
    # 2. Issue Type Analysis
    if ensure_tz_aware(total_consultations) > ensure_tz_aware(0):
        issue_counts = filtered_df['Issue'].value_counts()
        if len(issue_counts) > 0:
            top_issue = issue_counts.index[0]
            top_issue_pct = (issue_counts.iloc[0] / total_consultations) * 100
            
            insights.append({
                'type': 'pattern',
                'title': 'Primary Driver Identification',
                'description': f'"{top_issue}" dominates consultation volume, representing {top_issue_pct:.1f}% of all requests. This suggests focused training and resource allocation opportunities.',
                'impact': 'high',
                'metric': f'{issue_counts.iloc[0]:,} consultations'
            })
    
    # 3. Location-specific insights (when not filtering by location)
    if location == 'all' and total_consultations > 0:
        location_counts = filtered_df['Location'].value_counts()
        if len(location_counts) > 1:
            busiest_location = location_counts.index[0]
            busiest_count = location_counts.iloc[0]
            location_variance = (busiest_count / location_counts.mean() - 1) * 100
            
            if ensure_tz_aware(location_variance) > ensure_tz_aware(50):
                insights.append({
                    'type': 'location',
                    'title': 'Location Demand Imbalance',
                    'description': f'{busiest_location} handles {location_variance:.0f}% more consultations than average, suggesting resource reallocation opportunities.',
                    'impact': 'medium',
                    'metric': f'{busiest_count:,} consultations'
                })
    
    # 4. Technician Performance Analysis
    if ensure_tz_aware(total_consultations) > ensure_tz_aware(0):
        tech_performance = filtered_df.groupby('Technician Name').agg({
            'ID': 'count',
            'Consult Complete': lambda x: (x == 'Yes').sum()
        }).rename(columns={'ID': 'total', 'Consult Complete': 'completed'})
        
        if len(tech_performance) > 1:
            tech_performance['completion_rate'] = (tech_performance['completed'] / tech_performance['total']) * 100
            avg_completion_rate = tech_performance['completion_rate'].mean()
            top_performers = tech_performance[tech_performance['completion_rate'] > avg_completion_rate + 5]
            
            if len(top_performers) > 0:
                insights.append({
                    'type': 'performance',
                    'title': 'Technician Excellence',
                    'description': f'{len(top_performers)} technicians exceed average completion rates by 5%+. Their best practices could improve overall team performance.',
                    'impact': 'medium',
                    'metric': f'{avg_completion_rate:.1f}% avg completion'
                })
    
    # Return the insights
    return jsonify({
        'insights': insights,
        'total_insights': len(insights),
        'quarter': quarter,
        'location': location,
        'analysis_date': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
    })


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
@app.route('/api/technicians')
def api_technicians():
    """Get technicians data with incident counts by region"""
    if incidents_df is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    quarter = request.args.get('quarter', 'all')
    month = request.args.get('month', 'all')
    region = request.args.get('region', 'all')
    assignment_group = request.args.get('assignment_group', 'all')
    
    # Apply filters
    filtered_df = apply_filters(incidents_df, quarter, month, region, assignment_group)
    
    if len(filtered_df) == 0:
        return jsonify({
            'total_technicians': 0,
            'active_technicians': 0,
            'avg_incidents_per_tech': 0,
            'regions': []
        })
    
    # Get actual individual technician data from "Resolved by" field
    # Filter out incidents with null "Resolved by" values
    resolved_incidents = filtered_df[filtered_df['Resolved by'].notna()]
    
    if len(resolved_incidents) == 0:
        return jsonify({
            'total_technicians': 0,
            'active_technicians': 0,
            'avg_incidents_per_tech': 0,
            'regions': []
        })
    
    # Group by technician (Resolved by) and region
    tech_stats = resolved_incidents.groupby(['Resolved by', 'Region']).agg({
        'Number': 'count'
    }).reset_index()
    
    tech_stats['percentage'] = (tech_stats['Number'] / len(resolved_incidents) * 100).round(1)
    
    # Calculate summary stats
    total_technicians = resolved_incidents['Resolved by'].nunique()
    active_technicians = len(tech_stats[tech_stats['Number'] > 0])
    avg_incidents_per_tech = tech_stats['Number'].mean()
    
    # Group by region
    regions_data = []
    for region_name in tech_stats['Region'].unique():
        region_techs = tech_stats[tech_stats['Region'] == region_name]
        
        techs_list = []
        for _, row in region_techs.iterrows():
            # Clean technician names for display (remove ID if present)
            tech_display_name = row['Resolved by']
            # Remove the Walmart ID portion in parentheses for cleaner display
            if '(' in tech_display_name and ')' in tech_display_name:
                tech_display_name = tech_display_name.split('(')[0].strip()
            
            techs_list.append({
                'name': tech_display_name,
                'incidents': int(row['Number']),
                'percentage': f"{row['percentage']:.1f}"
            })
        
        # Sort technicians by incident count
        techs_list.sort(key=lambda x: x['incidents'], reverse=True)
        
        regions_data.append({
            'name': region_name,
            'technicians': techs_list
        })
    
    # Sort regions by total incidents
    regions_data.sort(key=lambda x: sum(t['incidents'] for t in x['technicians']), reverse=True)
    
    return jsonify({
        'total_technicians': total_technicians,
        'active_technicians': active_technicians, 
        'avg_incidents_per_tech': round(avg_incidents_per_tech, 1),
        'regions': regions_data
    })

@app.route('/api/locations')
def api_locations():
    """Get locations data with incident counts by region using proper region mapping"""
    if consultations_df is None or incidents_df is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    quarter = request.args.get('quarter', 'all')
    region = request.args.get('region', 'all')
    
    # For locations, use consultation data as it has actual location information
    filtered_consultations = apply_consultation_filters(consultations_df, quarter, None)
    
    # Also get the proper region mapping from incidents data
    filtered_incidents = apply_filters(incidents_df, quarter, region, None)
    
    if len(filtered_consultations) == 0:
        return jsonify({
            'total_locations': 0,
            'active_locations': 0,
            'avg_incidents_per_location': 0,
            'regions': []
        })
    
    # Group consultations by location
    location_stats = filtered_consultations.groupby('Location').agg({
        'Created': 'count'
    }).reset_index()
    location_stats.columns = ['Location', 'Consultations']
    location_stats['percentage'] = (location_stats['Consultations'] / len(filtered_consultations) * 100).round(1)
    
    # Get the proper region mapping from incidents data
    # Create a mapping of assignment groups to regions
    if 'Region' in incidents_df.columns:
        region_mapping = incidents_df[['Assignment group', 'Region']].drop_duplicates()
        assignment_to_region = dict(zip(region_mapping['Assignment group'], region_mapping['Region']))
    else:
        # Fallback to basic pattern matching if region mapping not available
        assignment_to_region = {}
    
    # Create a location to region mapping based on known patterns and incident data
    location_to_region = {}
    
    # Use the established region mapping from incidents data to categorize locations
    # This is more accurate than pattern matching
    for location in location_stats['Location'].unique():
        # Default region assignment based on location patterns
        if 'Puerto Rico' in str(location) or 'International' in str(location):
            location_to_region[location] = 'Puerto Rico'
        elif any(keyword in str(location).upper() for keyword in ['IDC', 'INDIA', 'BANGALORE', 'HYDERABAD', 'CHENNAI', 'MUMBAI', 'DELHI', 'PUNE']):
            location_to_region[location] = 'IDC'
        else:
            location_to_region[location] = 'US'
    
    # Calculate summary stats
    total_locations = len(location_stats)
    active_locations = len(location_stats[location_stats['Consultations'] > 0])
    avg_consultations_per_location = location_stats['Consultations'].mean()
    
    # Group locations by regions using proper mapping
    regions_data = []
    
    # Get unique regions from the mapping
    unique_regions = set(location_to_region.values())
    
    for region_name in sorted(unique_regions):
        region_locations = location_stats[location_stats['Location'].map(location_to_region) == region_name]
    
        if len(region_locations) > 0:
            locations_list = []
            for _, row in region_locations.iterrows():
                locations_list.append({
                'name': row['Location'], 
                'incidents': int(row['Consultations']),
                'percentage': f"{row['percentage']:.1f}"
            })
            
            # Sort by incident count (descending)
            locations_list.sort(key=lambda x: x['incidents'], reverse=True)
        
        regions_data.append({
                'name': region_name,
                'locations': locations_list
        })
    
    # Sort regions by total incidents (descending)
    regions_data.sort(key=lambda x: sum(l['incidents'] for l in x['locations']), reverse=True)
    
    return jsonify({
        'total_locations': total_locations,
        'active_locations': active_locations,
        'avg_incidents_per_location': avg_consultations_per_location,
        'regions': regions_data
    })

# Add new API endpoint for consultation type drill-down after the existing consultation endpoints
@app.route('/api/consultations/type-drilldown')
def api_consultations_type_drilldown():
    """Get detailed consultation type breakdown for drill-down modals"""
    if consultations_df is None:
        return jsonify({'error': 'Consultation data not loaded'}), 500
    
    quarter = request.args.get('quarter', 'all')
    location = request.args.get('location', 'all')
    region = request.args.get('region', 'all')
    consultation_type = request.args.get('type')  # The specific consultation type to drill down into
    technician_filter = request.args.get('technician', 'all')  # New: technician filter
    
    if not consultation_type:
        return jsonify({'error': 'Consultation type parameter required'}), 400
    
    # Apply filters
    filtered_df = apply_consultation_filters(consultations_df, quarter, location, region)
    
    # Apply technician filter if specified
    if technician_filter and technician_filter != 'all':
        filtered_df = filtered_df[filtered_df['Technician Name'] == technician_filter]
    
    # Filter by consultation type from 'Consultation Defined' field
    # Include ALL consultations for analysis (completed and uncompleted)
    type_df = filtered_df[filtered_df['Consultation Defined'] == consultation_type]
    completed_type_df = type_df[type_df['Consult Complete'] == 'Yes']
    
    if len(type_df) == 0:
        return jsonify({'error': f'No data found for consultation type: {consultation_type}'}), 404
    
    # Summary statistics
    total_consultations = len(type_df)
    completed_consultations = len(completed_type_df)
    uncompleted_consultations = total_consultations - completed_consultations
    completion_rate = (completed_consultations / total_consultations) * 100 if total_consultations > 0 else 0
    
    # INC creation analysis for this type (from completed consultations)
    inc_created = completed_type_df['INC %23'].notna().sum()
    inc_creation_rate = (inc_created / completed_consultations) * 100 if completed_consultations > 0 else 0
    
    # Special analysis for INC Created type
    enhanced_analysis = {}
    if consultation_type == 'INC Created':
        # Analyze uncompleted consultations
        uncompleted_df = type_df[type_df['Consult Complete'] != 'Yes']
        enhanced_analysis['uncompleted_details'] = []
        
        if len(uncompleted_df) > 0:
            uncompleted_analysis = uncompleted_df.groupby(['Technician Name', 'Consultation Defined']).size().reset_index(name='count')
            for _, row in uncompleted_analysis.iterrows():
                enhanced_analysis['uncompleted_details'].append({
                    'technician': str(row['Technician Name']),
                    'consultation_type': str(row['Consultation Defined']),
                    'count': int(row['count'])
                })
        
        # Get all technicians for filter dropdown from ORIGINAL data (before technician filter)
        original_filtered_df = apply_consultation_filters(consultations_df, quarter, location)
        original_type_df = original_filtered_df[original_filtered_df['Consultation Defined'] == consultation_type]
        all_technicians = original_type_df['Technician Name'].unique().tolist()
        enhanced_analysis['available_technicians'] = [str(tech) for tech in sorted(all_technicians)]
        enhanced_analysis['current_technician_filter'] = technician_filter
    
    # Type-specific analysis
    type_specific_metrics = generate_type_specific_metrics(completed_type_df, consultation_type)
    
    # Enhanced technician breakdown for this consultation type
    tech_stats = type_df.groupby('Technician Name').agg({
        'ID': 'count',  # Total consultations (completed + uncompleted)
        'INC %23': lambda x: x.notna().sum(),
        'Created': ['min', 'max'],
        'Location': lambda x: x.value_counts().index[0] if len(x) > 0 else 'N/A',  # Most common location
        'Consult Complete': lambda x: (x == 'Yes').sum()  # Completed consultations
    })
    
    # Add delta analysis (monthly trends per technician)
    tech_monthly_trends = {}
    if consultation_type == 'INC Created':
        for technician in type_df['Technician Name'].unique():
            tech_data = type_df[type_df['Technician Name'] == technician]
            monthly_counts = tech_data.groupby(tech_data['Created'].dt.to_period('M')).size()
            
            if len(monthly_counts) >= 2:
                # Calculate delta between last two months
                recent_months = monthly_counts.tail(2)
                if len(recent_months) == 2:
                    delta = recent_months.iloc[1] - recent_months.iloc[0]
                    delta_percentage = (delta / recent_months.iloc[0] * 100) if recent_months.iloc[0] > 0 else 0
                    tech_monthly_trends[technician] = {
                        'current_month': int(recent_months.iloc[1]),
                        'previous_month': int(recent_months.iloc[0]),
                        'delta': int(delta),
                        'delta_percentage': float(delta_percentage)
                    }
                else:
                    tech_monthly_trends[technician] = {
                        'current_month': int(monthly_counts.iloc[0]),
                        'previous_month': 0,
                        'delta': int(monthly_counts.iloc[0]),
                        'delta_percentage': 100.0
                    }
            else:
                tech_monthly_trends[technician] = {
                    'current_month': int(monthly_counts.iloc[0]) if len(monthly_counts) > 0 else 0,
                    'previous_month': 0,
                    'delta': int(monthly_counts.iloc[0]) if len(monthly_counts) > 0 else 0,
                    'delta_percentage': 100.0 if len(monthly_counts) > 0 else 0.0
                }
    
    # Flatten column names
    tech_stats.columns = ['total_consultations', 'inc_created', 'first_consultation', 'last_consultation', 'primary_location', 'completed_consultations']
    tech_stats['completion_rate'] = (tech_stats['completed_consultations'] / tech_stats['total_consultations']) * 100
    tech_stats['inc_creation_rate'] = (tech_stats['inc_created'] / tech_stats['completed_consultations']) * 100
    tech_stats = tech_stats.sort_values('total_consultations', ascending=False)
    
    # Prepare enhanced technician data
    technicians = []
    for tech_name, stats in tech_stats.iterrows():
        # Get monthly trend data for this technician
        monthly_trend = tech_monthly_trends.get(tech_name, {
            'current_month': 0,
            'previous_month': 0,
            'delta': 0,
            'delta_percentage': 0.0
        })
        
        # Get uncompleted consultations for this technician
        tech_uncompleted = type_df[(type_df['Technician Name'] == tech_name) & (type_df['Consult Complete'] != 'Yes')]
        uncompleted_count = len(tech_uncompleted)
        
        technicians.append({
            'technician_name': str(tech_name),
            'total_consultations': int(stats['total_consultations']),
            'completed_consultations': int(stats['completed_consultations']),
            'uncompleted_consultations': int(uncompleted_count),
            'completion_rate': round(float(stats['completion_rate']), 1),
            'inc_created': int(stats['inc_created']),
            'inc_creation_rate': round(float(stats['inc_creation_rate']), 1) if stats['completed_consultations'] > 0 else 0,
            'primary_location': str(stats['primary_location']),
            'first_consultation': stats['first_consultation'].strftime('%Y-%m-%d'),
            'last_consultation': stats['last_consultation'].strftime('%Y-%m-%d'),
            'percentage_of_type': round(float(stats['total_consultations']) / float(total_consultations) * 100, 1),
            'monthly_delta': monthly_trend['delta'],
            'monthly_delta_percentage': round(monthly_trend['delta_percentage'], 1),
            'current_month_count': monthly_trend['current_month'],
            'previous_month_count': monthly_trend['previous_month']
        })
    
    # Location breakdown for this consultation type
    location_stats = type_df.groupby('Location').agg({
        'ID': 'count',
        'INC %23': lambda x: x.notna().sum(),
        'Technician Name': 'nunique'
    }).rename(columns={'ID': 'total_consultations', 'INC %23': 'inc_created', 'Technician Name': 'unique_technicians'})
    
    location_stats['inc_creation_rate'] = (location_stats['inc_created'] / location_stats['total_consultations']) * 100
    location_stats = location_stats.sort_values('total_consultations', ascending=False)
    
    locations = []
    for location_name, stats in location_stats.iterrows():
        locations.append({
            'location': str(location_name),
            'total_consultations': int(stats['total_consultations']),
            'inc_created': int(stats['inc_created']),
            'inc_creation_rate': round(float(stats['inc_creation_rate']), 1),
            'unique_technicians': int(stats['unique_technicians']),
            'percentage_of_type': round(float(stats['total_consultations']) / float(total_consultations) * 100, 1)
        })
    
    # Monthly trends for this consultation type
    monthly_stats = type_df.groupby(type_df['Created'].dt.to_period('M')).agg({
        'ID': 'count',
        'INC %23': lambda x: x.notna().sum()
    }).rename(columns={'ID': 'total_consultations', 'INC %23': 'inc_created'})
    
    monthly_trends = []
    for period, stats in monthly_stats.iterrows():
        inc_rate = (float(stats['inc_created']) / float(stats['total_consultations'])) * 100 if stats['total_consultations'] > 0 else 0
        monthly_trends.append({
            'month': period.strftime('%b %Y'),
            'total_consultations': int(stats['total_consultations']),
            'inc_created': int(stats['inc_created']),
            'inc_creation_rate': round(float(inc_rate), 1)
        })
    
    # Sample consultation records (most recent 20)
    sample_consultations = type_df.nlargest(20, 'Created')[
        ['ID', 'Created', 'Technician Name', 'Location', 'Issue', 'INC %23']
    ].copy()
    
    consultation_samples = []
    for _, consultation in sample_consultations.iterrows():
        consultation_samples.append({
            'id': str(consultation['ID']),
            'created': consultation['Created'].strftime('%Y-%m-%d %H:%M'),
            'technician': str(consultation['Technician Name']),
            'location': str(consultation['Location']),
            'issue': consultation['Issue'][:100] + '...' if len(str(consultation['Issue'])) > 100 else str(consultation['Issue']),
            'inc_number': str(consultation['INC %23']) if pd.notna(consultation['INC %23']) else 'No INC',
            'has_inc': bool(pd.notna(consultation['INC %23']))
        })
    
    # Generate insights for this consultation type using type-specific metrics
    insights = generate_type_specific_insights(consultation_type, type_specific_metrics, technicians, locations, inc_creation_rate, inc_created, total_consultations)
    
    return jsonify({
        'status': 'success',
        'consultation_type': consultation_type,
        'filters': {
            'quarter': quarter,
            'location': location,
            'technician': technician_filter
        },
        'summary': {
            'total_consultations': int(total_consultations),
            'completed_consultations': int(completed_consultations),
            'uncompleted_consultations': int(uncompleted_consultations),
            'completion_rate': round(float(completion_rate), 1),
            'inc_created': int(inc_created),
            'inc_creation_rate': round(float(inc_creation_rate), 1),
            'unique_technicians': int(len(technicians)),
            'unique_locations': int(len(locations)),
            'date_range': {
                'start': type_df['Created'].min().strftime('%Y-%m-%d'),
                'end': type_df['Created'].max().strftime('%Y-%m-%d')
            },
            'type_specific': type_specific_metrics
        },
        'enhanced_analysis': enhanced_analysis,
        'technicians': technicians,
        'locations': locations,
        'monthly_trends': monthly_trends,
        'consultation_samples': consultation_samples,
        'insights': insights
    })

# Add new API endpoint for invalid INC analysis after the existing consultation endpoints

@app.route('/api/consultations/invalid-inc-analysis')
def api_consultations_invalid_inc_analysis():
    """Get detailed analysis of invalid INC numbers in INC Created consultations - OPTIMIZED VERSION"""
    if consultations_df is None or incidents_df is None:
        return jsonify({'error': 'Data not loaded'}), 500
    
    quarter = request.args.get('quarter', 'all')
    location = request.args.get('location', 'all')
    region = request.args.get('region', 'all')
    technician = request.args.get('technician', 'all')
    
    try:
        # Apply filters
        filtered_df = apply_consultation_filters(consultations_df, quarter, location, region)
        
        # Apply technician filter if specified
        if technician and technician != 'all':
            filtered_df = filtered_df[filtered_df['Technician Name'] == technician]
        
        # Focus on "INC Created" consultations only
        completed_df = filtered_df[filtered_df['Consult Complete'] == 'Yes']
        inc_created_df = completed_df[completed_df['Consultation Defined'] == 'INC Created']
    
        if len(inc_created_df) == 0:
            return jsonify({'error': 'No INC Created consultations found'}), 404
    
        # Get consultations with INC numbers
        consultations_with_inc = inc_created_df[inc_created_df['INC %23'].notna()].copy()
    
        if len(consultations_with_inc) == 0:
            return jsonify({'error': 'No consultations with INC numbers found'}), 404
        
        # Clean INC numbers (remove extra whitespace, tabs, etc.)
        consultations_with_inc['INC_cleaned'] = consultations_with_inc['INC %23'].astype(str).str.strip()
        
        # Fast validation using vectorized operations
        valid_incident_numbers = set(incidents_df['Number'].astype(str).str.strip())
        consultations_with_inc['is_valid'] = consultations_with_inc['INC_cleaned'].isin(valid_incident_numbers)
        
        # Count valid/invalid
        valid_count = consultations_with_inc['is_valid'].sum()
        invalid_count = len(consultations_with_inc) - valid_count
        
        # Get invalid samples with detailed analysis 
        # If technician filter is applied, get ALL invalid samples for that technician
        # Otherwise, limit to 100 for performance (increased from 20)
        invalid_samples_df = consultations_with_inc[~consultations_with_inc['is_valid']]
        if technician and technician != 'all':
            # Get ALL invalid samples for the specific technician
            invalid_samples = invalid_samples_df[invalid_samples_df['Technician Name'] == technician]
        else:
            # Limit to 100 samples for general overview
            invalid_samples = invalid_samples_df.head(100)
        
        invalid_incs = []
        for _, consultation in invalid_samples.iterrows():
            invalid_reason = analyze_invalid_inc_reason(consultation['INC_cleaned'])
            invalid_incs.append({
                'consultation_id': str(consultation['ID']),
                'inc_number': consultation['INC_cleaned'],
                'technician': str(consultation['Technician Name']),
                'location': str(consultation['Location']),
                'created': consultation['Created'].strftime('%Y-%m-%d %H:%M'),
                'issue': str(consultation['Issue'])[:100] + '...' if len(str(consultation['Issue'])) > 100 else str(consultation['Issue']),
                'reason': invalid_reason
            })
        
        # Detailed technician breakdown with assignment groups and primary issues
        if ensure_tz_aware(invalid_count) > ensure_tz_aware(0):
            tech_breakdown = consultations_with_inc[~consultations_with_inc['is_valid']].groupby('Technician Name').size().sort_values(ascending=False)
            technician_breakdown = []
            for tech, count in tech_breakdown.head(10).items():
                # Find assignment group for this technician
                assignment_group = 'Unknown'
                tech_incidents = incidents_df[incidents_df['Resolved by'].str.contains(tech, na=False, case=False)]
                if len(tech_incidents) > 0:
                    assignment_group = tech_incidents['Assignment group'].iloc[0]
                
                # Get primary issue for this technician - sample more to get better representation
                tech_invalid_samples = consultations_with_inc[
                    (~consultations_with_inc['is_valid']) & 
                    (consultations_with_inc['Technician Name'] == tech)
                ]
                
                primary_issue = 'Not found in database'
                if len(tech_invalid_samples) > 0:
                    # Sample up to 20 or all if less, with random sampling for better representation
                    sample_size = min(20, len(tech_invalid_samples))
                    if len(tech_invalid_samples) > sample_size:
                        tech_samples = tech_invalid_samples.sample(n=sample_size, random_state=42)
                    else:
                        tech_samples = tech_invalid_samples
                    
                    reason_counts = {}
                    for _, consultation in tech_samples.iterrows():
                        reason = analyze_invalid_inc_reason(consultation['INC_cleaned'])
                        reason_counts[reason] = reason_counts.get(reason, 0) + 1
                    # Get most common reason
                    if reason_counts:
                        primary_issue = max(reason_counts.items(), key=lambda x: x[1])[0]
                
                technician_breakdown.append({
                    'technician_name': tech,
                    'assignment_group': assignment_group,
                    'invalid_count': int(count),
                    'percentage_of_invalid': round((count / invalid_count) * 100, 1)
                })
        else:
            technician_breakdown = []
        
        # Detailed location breakdown
        if ensure_tz_aware(invalid_count) > ensure_tz_aware(0):
            location_breakdown_data = consultations_with_inc[~consultations_with_inc['is_valid']].groupby('Location').size().sort_values(ascending=False)
            location_breakdown = []
            for location, count in location_breakdown_data.head(10).items():
                # Get primary issue for this location - sample more to get better representation
                location_invalid_samples = consultations_with_inc[
                    (~consultations_with_inc['is_valid']) & 
                    (consultations_with_inc['Location'] == location)
                ]
                
                primary_issue = 'Not found in database'
                if len(location_invalid_samples) > 0:
                    # Sample up to 20 or all if less, with random sampling for better representation
                    sample_size = min(20, len(location_invalid_samples))
                    if len(location_invalid_samples) > sample_size:
                        location_samples = location_invalid_samples.sample(n=sample_size, random_state=42)
                    else:
                        location_samples = location_invalid_samples
                    
                    reason_counts = {}
                    for _, consultation in location_samples.iterrows():
                        reason = analyze_invalid_inc_reason(consultation['INC_cleaned'])
                        reason_counts[reason] = reason_counts.get(reason, 0) + 1
                    # Get most common reason
                    if reason_counts:
                        primary_issue = max(reason_counts.items(), key=lambda x: x[1])[0]
                
                location_breakdown.append({
                    'location': location,
                    'invalid_count': int(count),
                    'percentage_of_invalid': round((count / invalid_count) * 100, 1),
                    'primary_issue': primary_issue
                })
        else:
            location_breakdown = []
        
        # Simple response
        return jsonify({
            'status': 'success',
            'filters': {
                'quarter': quarter,
                'location': location,
                'region': region,
                'technician': technician
            },
            'summary': {
                'total_inc_created': len(inc_created_df),
                'total_with_inc_numbers': len(consultations_with_inc),
                'valid_inc_count': int(valid_count),
                'invalid_inc_count': int(invalid_count),
                'validation_rate': round((valid_count / len(consultations_with_inc)) * 100, 1),
                'data_quality_score': round((valid_count / len(consultations_with_inc)) * 100, 1)
            },
            'technician_breakdown': technician_breakdown,
            'location_breakdown': location_breakdown,
            'reason_breakdown': get_detailed_reason_breakdown(consultations_with_inc[~consultations_with_inc['is_valid']]),
            'invalid_samples': invalid_incs
        })
    
    except Exception as e:
        print(f"Error in invalid-inc-analysis: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


def get_detailed_reason_breakdown(invalid_consultations):
    """Get breakdown of reasons why INC numbers are invalid"""
    if len(invalid_consultations) == 0:
        return []
    
    reason_counts = {}
    total_invalid = len(invalid_consultations)
    
    # Analyze all invalid consultations for accurate breakdown
    for _, consultation in invalid_consultations.iterrows():
        reason = analyze_invalid_inc_reason(consultation['INC_cleaned'])
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    
    # Convert to list format sorted by count
    reason_breakdown = []
    for reason, count in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True):
        reason_breakdown.append({
            'reason': reason,
            'count': int(count),
            'percentage': round((count / total_invalid) * 100, 1)
        })
    
    return reason_breakdown

def analyze_invalid_inc_reason(inc_number):
    """Analyze why an INC number is invalid"""
    inc_str = str(inc_number).strip()
    
    # Check for common invalid patterns
    if not inc_str or inc_str.lower() in ['nan', 'none', 'null', '']:
        return 'Missing/Empty'
    elif not inc_str.startswith('INC'):
        return 'Invalid Format (No INC prefix)'
    elif len(inc_str) < 10:
        return 'Too Short (< 10 characters)'
    elif len(inc_str) > 15:
        return 'Too Long (> 15 characters)'
    elif not inc_str[3:].replace('\t', '').replace(' ', '').isdigit():
        return 'Contains Non-numeric Characters'
    elif '\t' in inc_str or '  ' in inc_str:
        return 'Contains Extra Whitespace/Tabs'
    else:
        return 'Not found in database'

@app.route('/api/consultations/location-region')
def api_consultations_location_region():
    """Get region for a specific location"""
    global consultations_df
    
    try:
        location = request.args.get('location', 'all')
        
        if ensure_tz_aware(location) == ensure_tz_aware('all'):
            return jsonify({
                'region': 'all'
            })
        
        # Find the region for this location
        location_data = consultations_df[consultations_df['Location'] == location]
        
        if len(location_data) > 0 and 'Region' in location_data.columns:
            # Get the most common region for this location (should be only one)
            region = location_data['Region'].value_counts().index[0]
            
            return jsonify({
                'region': region,
                'location': location
            })
        else:
            return jsonify({
                'region': 'all',
                'error': 'Location not found'
            })
            
    except Exception as e:
        print(f"Error in location-region API: {e}")
        return jsonify({
            'error': str(e)
        }), 500

if ensure_tz_aware(__name__) == ensure_tz_aware('__main__'):
    import socket
    import time
    import atexit
    
    def check_port_available(port):
        """Check if a port is available"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(('127.0.0.1', port))
                return True
            except OSError:
                return False
    
    def cleanup_memory():
        # Add memory management here
        pass
    
    def cleanup():
        # Enhanced cleanup function
        print("\n🛑 Shutting down dashboard...")
        cleanup_memory()
        print("✅ Cleanup completed")
    
    # Register cleanup function
    atexit.register(cleanup)
    
    # Load data on startup
    success = load_data()
    if not success:
        print("⚠️ Starting with limited functionality due to data loading issues")
    
    # Create error template if it doesn't exist
    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    error_template_path = os.path.join(templates_dir, 'error.html')
    if not os.path.exists(error_template_path):
        os.makedirs(templates_dir, exist_ok=True)
        with open(error_template_path, 'w') as f:
            f.write('''<!DOCTYPE html>
<html>
<head>
    <title>Error - MBR Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f8f9fa; }
        .error-container { max-width: 800px; margin: 50px auto; padding: 30px; background: white; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #dc3545; }
        .btn { display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="error-container">
        <h1>⚠️ An error occurred</h1>
        <p>We apologize for the inconvenience. The following error was encountered:</p>
        <pre>{{ error }}</pre>
        <p>Please try refreshing the page or contact support if the issue persists.</p>
        <a href="/" class="btn">Return to Dashboard</a>
    </div>
</body>
</html>''')
    
    # Find available port starting from 8080
    port = 8080
    while not check_port_available(port):
        print(f"Port {port} is in use, trying {port+1}")
        port += 1
    
    print(f"🚀 Starting MBR Dashboard on port {port}...")
    print(f"🌐 Open your browser to: http://127.0.0.1:{port}")
    print("   Press Ctrl+C to stop the server")
    
    try:
        # Start the Flask application
        app.run(host='0.0.0.0', port=port, use_reloader=False)
    except KeyboardInterrupt:
        print("\n✅ Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        exit(1)