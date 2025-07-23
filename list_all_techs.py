import pandas as pd
import os

print("Listing all technicians in the dashboard...")

# Load consultations data
consultations_file = 'Pre-TSQ Data-FebTOJune2025.xlsx'
consultations_df = pd.read_excel(consultations_file, sheet_name='Pre-TSQ Data (6)')

# Apply the same filters as in app.py
consultations_df['Technician Name'] = consultations_df['Technician Name'].fillna('Unknown')

# Filter to match incident data timeframe (February-June only, exclude January and July)
consultations_df = consultations_df[
    (consultations_df['Created'].dt.month >= 2) & 
    (consultations_df['Created'].dt.month <= 6)
]

# Filter out "Virtual Tech Spot Reservation (TECH USE ONLY)"
consultations_df = consultations_df[consultations_df['Location'] != "Virtual Tech Spot Reservation (TECH USE ONLY)"]

# Get unique technicians and sort alphabetically
techs = sorted(consultations_df['Technician Name'].unique())

# Count consultations per technician
tech_counts = consultations_df['Technician Name'].value_counts().sort_values(ascending=False)

# Print the list of technicians with their consultation counts
print(f"\nTotal technicians: {len(techs)}")
print("\nAll technicians (sorted by consultation count):")
for tech, count in tech_counts.items():
    print(f"- {tech}: {count} consultations")

# Separate vendor and non-vendor technicians
vendor_techs = [tech for tech in techs if 'Vendor' in str(tech)]
non_vendor_techs = [tech for tech in techs if 'Vendor' not in str(tech)]

print(f"\nVendor technicians: {len(vendor_techs)}")
print(f"Non-vendor technicians: {len(non_vendor_techs)}") 