import pandas as pd

# Load the data
df = pd.read_excel('Pre-TSQ Data-FebTOJune2025.xlsx', sheet_name='Pre-TSQ Data (6)')
df['Created'] = pd.to_datetime(df['Created'])

# Print overall date range
print(f'Full date range: {df["Created"].min()} to {df["Created"].max()}')

# Check each month
for month in range(1, 7):
    month_data = df[df['Created'].dt.month == month]
    if not month_data.empty:
        print(f'Month {month} date range: {month_data["Created"].min()} to {month_data["Created"].max()}, count: {len(month_data)}') 