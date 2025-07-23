import pandas as pd

# Load the incidents data
try:
    incidents_df = pd.read_excel('Combined_Incidents_Report_Feb_to_June_2025.xlsx')
    
    # Convert date columns
    incidents_df['Created'] = pd.to_datetime(incidents_df['Created'])
    
    # Print overall date range
    print(f'Incidents full date range: {incidents_df["Created"].min()} to {incidents_df["Created"].max()}')
    
    # Check each month
    for month in range(1, 7):
        month_data = incidents_df[incidents_df['Created'].dt.month == month]
        if not month_data.empty:
            print(f'Month {month} date range: {month_data["Created"].min()} to {month_data["Created"].max()}, count: {len(month_data)}')
except Exception as e:
    print(f"Error loading incidents data: {e}") 