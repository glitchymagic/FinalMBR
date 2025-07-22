#!/usr/bin/env python3
import pandas as pd
import os

print('🔍 ANALYZING NEW CONSULTATION DATA STRUCTURE')
print('=' * 50)

base_path = '/Users/j0j0ize/Downloads/finalMBR-1/static/Pre-TSQ Data'

# Check each region folder
regions = []
sample_data = None
sample_columns = None

for item in os.listdir(base_path):
    region_path = os.path.join(base_path, item)
    if os.path.isdir(region_path):
        regions.append(item)
        print(f'📁 Region: {item}')
        
        # List files in this region
        files = [f for f in os.listdir(region_path) if f.endswith('.xlsx') and not f.startswith('~')]
        print(f'   Files: {len(files)} Excel files')
        
        for file in sorted(files):
            file_path = os.path.join(region_path, file)
            try:
                # Try to read the first file to understand structure
                df = pd.read_excel(file_path)
                print(f'   ✅ {file}: {len(df)} rows, {len(df.columns)} columns')
                
                if len(df) > 0 and sample_data is None:
                    sample_data = df.head(3)
                    sample_columns = list(df.columns)
                    print(f'      Columns: {sample_columns}')
                    
                break  # Just check first file per region
            except Exception as e:
                print(f'   ❌ {file}: Error - {str(e)[:50]}')
        print()

print(f'📊 SUMMARY: {len(regions)} regions found')
for region in sorted(regions):
    print(f'   - {region}')

if sample_data is not None:
    print(f'\n📋 SAMPLE DATA STRUCTURE:')
    print(f'Columns ({len(sample_columns)}): {sample_columns}')
    print(f'\nFirst 3 rows:')
    print(sample_data.to_string())
else:
    print('\n⚠️ No sample data could be loaded')
