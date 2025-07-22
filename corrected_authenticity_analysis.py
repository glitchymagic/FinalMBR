import pandas as pd
import numpy as np
from datetime import datetime
import re
from collections import Counter

def corrected_authenticity_analysis():
    print('🔍 CORRECTED DATA AUTHENTICITY ANALYSIS - CONSULTATION DATA')
    print('=' * 70)
    
    # Load the consultation data
    df = pd.read_excel('Pre-TSQ Data-FebTOJune2025.xlsx')
    print(f'✅ Successfully loaded consultation data: {len(df)} records')
    print(f'📊 Dataset: Consultation/Tech Support data (NOT incident data)')
    print()
    
    # 1. INC NUMBER AUTHENTICITY (using correct column)
    print('🎫 INC NUMBER AUTHENTICITY:')
    inc_column = 'INC %23'
    if inc_column in df.columns:
        inc_numbers = df[inc_column].dropna()
        print(f'  📋 Total INC numbers: {len(inc_numbers)}')
        
        # Check INC format
        inc_pattern = re.compile(r'^INC\d{8}$')
        valid_inc = inc_numbers.str.match(inc_pattern, na=False).sum()
        print(f'  ✅ Valid INC format: {valid_inc}/{len(inc_numbers)} ({valid_inc/len(inc_numbers)*100:.1f}%)')
        
        # Check for sequential patterns
        numeric_parts = inc_numbers.str.extract(r'INC(\d{8})')[0].astype(int, errors='ignore')
        numeric_parts = numeric_parts.dropna()
        if len(numeric_parts) > 1:
            differences = numeric_parts.diff().dropna()
            sequential_count = (differences == 1).sum()
            print(f'  🔢 Sequential INC numbers: {sequential_count}/{len(differences)} ({sequential_count/len(differences)*100:.1f}%)')
            if sequential_count / len(differences) < 0.05:
                print('  ✅ LOW SEQUENTIAL PATTERN - Indicates real operational data')
            else:
                print('  ⚠️  HIGH SEQUENTIAL PATTERN - May indicate demo data')
    
    # 2. TECHNICIAN NAME AUTHENTICITY
    print('\n👥 TECHNICIAN NAME AUTHENTICITY:')
    name_columns = ['Technician Name', 'Name', 'Created By', 'Modified By']
    all_names = set()
    
    for col in name_columns:
        if col in df.columns:
            names = df[col].dropna().unique()
            all_names.update(names)
            print(f'  📝 {col}: {len(names)} unique names')
    
    print(f'  👤 Total unique people: {len(all_names)}')
    
    # Check for suspicious demo patterns
    demo_patterns = ['test', 'demo', 'sample', 'placeholder', 'user', 'admin', 'temp']
    suspicious_names = []
    for name in all_names:
        name_lower = str(name).lower()
        if any(pattern in name_lower for pattern in demo_patterns):
            suspicious_names.append(name)
    
    print(f'  🚨 Suspicious demo names: {len(suspicious_names)}')
    if suspicious_names:
        print(f'    Examples: {suspicious_names[:5]}')
    else:
        print('  ✅ No suspicious demo patterns detected')
    
    # Show sample real names
    sample_names = [name for name in list(all_names)[:10] if isinstance(name, str)]
    print(f'  📝 Sample names: {sample_names[:5]}')
    
    # 3. DATE AUTHENTICITY
    print('\n📅 DATE AUTHENTICITY:')
    date_columns = ['Created', 'Modified']
    for col in date_columns:
        if col in df.columns:
            dates = pd.to_datetime(df[col], errors='coerce').dropna()
            if len(dates) > 0:
                date_range = dates.max() - dates.min()
                print(f'  📆 {col}: {len(dates)} valid dates, range: {date_range.days} days')
                print(f'    From: {dates.min().strftime("%Y-%m-%d")} To: {dates.max().strftime("%Y-%m-%d")}')
                
                # Check for weekend patterns
                weekend_incidents = dates[dates.dt.weekday >= 5].count()
                weekday_incidents = dates[dates.dt.weekday < 5].count()
                if weekday_incidents > 0:
                    weekend_ratio = weekend_incidents / (weekend_incidents + weekday_incidents)
                    print(f'    📅 Weekend ratio: {weekend_ratio:.1%} (realistic if < 30%)')
    
    # 4. LOCATION AUTHENTICITY
    print('\n🌍 LOCATION AUTHENTICITY:')
    if 'Location' in df.columns:
        locations = df['Location'].dropna().unique()
        print(f'  📍 Unique locations: {len(locations)}')
        print(f'  📝 Sample locations: {list(locations)[:5]}')
        
        # Check for realistic location names
        realistic_locations = 0
        for loc in locations:
            if isinstance(loc, str) and (len(loc) > 3 and not loc.lower().startswith('test')):
                realistic_locations += 1
        print(f'  ✅ Realistic locations: {realistic_locations}/{len(locations)} ({realistic_locations/len(locations)*100:.1f}%)')
    
    # 5. BUSINESS PROCESS AUTHENTICITY
    print('\n💼 BUSINESS PROCESS AUTHENTICITY:')
    if 'Issue' in df.columns:
        issues = df['Issue'].dropna().unique()
        print(f'  📋 Issue types: {len(issues)}')
        print(f'  📝 Sample issues: {list(issues)[:3]}')
    
    if 'Consult Complete' in df.columns:
        completion_status = df['Consult Complete'].value_counts()
        print(f'  ✅ Completion status: {dict(completion_status)}')
    
    # 6. TIME DISTRIBUTION ANALYSIS
    print('\n⏰ TIME DISTRIBUTION ANALYSIS:')
    if 'Created' in df.columns:
        created_times = pd.to_datetime(df['Created'], errors='coerce').dropna()
        if len(created_times) > 0:
            hours = created_times.dt.hour
            hour_counts = hours.value_counts().sort_index()
            peak_hour = hour_counts.idxmax()
            peak_count = hour_counts.max()
            print(f'  ⏰ Peak hour: {peak_hour}:00 ({peak_count} consultations)')
            
            # Check for realistic business hours pattern
            business_hours = hour_counts[8:18].sum()
            total_hours = hour_counts.sum()
            business_ratio = business_hours / total_hours
            print(f'  🏢 Business hours (8-18): {business_ratio:.1%} of consultations')
    
    # 7. FINAL AUTHENTICITY SCORING
    print('\n🎯 AUTHENTICITY ASSESSMENT:')
    authenticity_score = 0
    max_score = 0
    
    # INC format check
    if inc_column in df.columns:
        inc_numbers = df[inc_column].dropna()
        if len(inc_numbers) > 0:
            inc_pattern = re.compile(r'^INC\d{8}$')
            valid_inc = inc_numbers.str.match(inc_pattern, na=False).sum()
            if valid_inc/len(inc_numbers) > 0.95:
                authenticity_score += 20
                print('  ✅ INC format: +20 points')
        max_score += 20
    
    # Low sequential pattern
    if inc_column in df.columns:
        inc_numbers = df[inc_column].dropna()
        if len(inc_numbers) > 1:
            numeric_parts = inc_numbers.str.extract(r'INC(\d{8})')[0].astype(int, errors='ignore')
            numeric_parts = numeric_parts.dropna()
            if len(numeric_parts) > 1:
                differences = numeric_parts.diff().dropna()
                sequential_count = (differences == 1).sum()
                if sequential_count/len(differences) < 0.05:
                    authenticity_score += 20
                    print('  ✅ Non-sequential INC numbers: +20 points')
        max_score += 20
    
    # No suspicious names
    if len(suspicious_names) == 0:
        authenticity_score += 20
        print('  ✅ No suspicious names: +20 points')
    max_score += 20
    
    # Realistic date range
    if 'Created' in df.columns:
        created_dates = pd.to_datetime(df['Created'], errors='coerce').dropna()
        if len(created_dates) > 0:
            date_range = created_dates.max() - created_dates.min()
            if date_range.days > 30:
                authenticity_score += 20
                print('  ✅ Realistic date range: +20 points')
        max_score += 20
    
    # Realistic locations
    if 'Location' in df.columns:
        locations = df['Location'].dropna().unique()
        realistic_locations = 0
        for loc in locations:
            if isinstance(loc, str) and (len(loc) > 3 and not loc.lower().startswith('test')):
                realistic_locations += 1
        if realistic_locations/len(locations) > 0.8:
            authenticity_score += 20
            print('  ✅ Realistic locations: +20 points')
        max_score += 20
    
    final_score = (authenticity_score / max_score) * 100 if max_score > 0 else 0
    print(f'\n🏆 FINAL AUTHENTICITY SCORE: {final_score:.1f}% ({authenticity_score}/{max_score})')
    
    if final_score >= 90:
        print('🎉 VERDICT: HIGH CONFIDENCE - AUTHENTIC PRODUCTION DATA')
    elif final_score >= 70:
        print('✅ VERDICT: LIKELY AUTHENTIC - PRODUCTION DATA')
    elif final_score >= 50:
        print('⚠️  VERDICT: MIXED SIGNALS - NEEDS INVESTIGATION')
    else:
        print('🚨 VERDICT: LIKELY DEMO/TEST DATA')
    
    print('\n📋 IMPORTANT CLARIFICATION:')
    print('This is CONSULTATION data (tech support requests), not incident resolution data.')
    print('The dashboard shows consultation metrics, which is legitimate business data.')
    
    return final_score

# Run the corrected analysis
if __name__ == "__main__":
    corrected_authenticity_analysis()
