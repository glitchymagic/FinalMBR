import pandas as pd
import numpy as np
from datetime import datetime
import re
from collections import Counter

def comprehensive_data_authenticity_analysis():
    print('🔍 COMPREHENSIVE DATA AUTHENTICITY DUE DILIGENCE')
    print('=' * 70)
    
    # Load the main data file
    try:
        df = pd.read_excel('Pre-TSQ Data-FebTOJune2025.xlsx')
        print(f'✅ Successfully loaded data file: {len(df)} records')
    except Exception as e:
        print(f'❌ Error loading data: {e}')
        return
    
    print(f'📊 Dataset Overview: {len(df)} records, {len(df.columns)} columns')
    print(f'📅 Date Range: {df.columns[0] if len(df.columns) > 0 else "Unknown"}')
    
    # 1. INCIDENT NUMBER AUTHENTICITY CHECK
    print('\n🎫 INCIDENT NUMBER AUTHENTICITY:')
    if 'Number' in df.columns:
        incident_numbers = df['Number'].dropna()
        print(f'  📋 Total incidents with numbers: {len(incident_numbers)}')
        
        # Check INC format
        inc_pattern = re.compile(r'^INC\d{8}$')
        valid_inc = incident_numbers.str.match(inc_pattern, na=False).sum()
        print(f'  ✅ Valid INC format: {valid_inc}/{len(incident_numbers)} ({valid_inc/len(incident_numbers)*100:.1f}%)')
        
        # Check for sequential patterns (demo data often has sequential numbers)
        numeric_parts = incident_numbers.str.extract(r'INC(\d{8})')[0].astype(int, errors='ignore')
        numeric_parts = numeric_parts.dropna()
        if len(numeric_parts) > 1:
            differences = numeric_parts.diff().dropna()
            sequential_count = (differences == 1).sum()
            print(f'  🔢 Sequential incidents: {sequential_count}/{len(differences)} ({sequential_count/len(differences)*100:.1f}%)')
            if sequential_count / len(differences) > 0.1:
                print('  ⚠️  HIGH SEQUENTIAL PATTERN - May indicate demo data')
            else:
                print('  ✅ LOW SEQUENTIAL PATTERN - Indicates real operational data')
    
    # 2. TECHNICIAN NAME AUTHENTICITY
    print('\n👥 TECHNICIAN NAME AUTHENTICITY:')
    name_columns = ['Resolved by', 'Assigned to', 'Caller']
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
    
    # Check name formatting (real names usually have proper case)
    proper_names = 0
    for name in list(all_names)[:20]:  # Sample first 20
        if isinstance(name, str) and name.replace(' ', '').replace('-', '').isalpha():
            if name.istitle() or ' ' in name:
                proper_names += 1
    
    print(f'  📝 Proper name formatting: {proper_names}/20 sample names ({proper_names/20*100:.1f}%)')
    
    # 3. DATE AUTHENTICITY
    print('\n📅 DATE AUTHENTICITY:')
    date_columns = ['Created', 'Resolved', 'Updated']
    for col in date_columns:
        if col in df.columns:
            dates = pd.to_datetime(df[col], errors='coerce').dropna()
            if len(dates) > 0:
                date_range = dates.max() - dates.min()
                print(f'  📆 {col}: {len(dates)} valid dates, range: {date_range.days} days')
                print(f'    From: {dates.min().strftime("%Y-%m-%d")} To: {dates.max().strftime("%Y-%m-%d")}')
                
                # Check for realistic distribution
                daily_counts = dates.dt.date.value_counts()
                avg_per_day = daily_counts.mean()
                std_per_day = daily_counts.std()
                print(f'    📊 Avg per day: {avg_per_day:.1f}, Std dev: {std_per_day:.1f}')
                
                # Check for weekend patterns (real data often has fewer weekend incidents)
                weekend_incidents = dates[dates.dt.weekday >= 5].count()
                weekday_incidents = dates[dates.dt.weekday < 5].count()
                if weekday_incidents > 0:
                    weekend_ratio = weekend_incidents / (weekend_incidents + weekday_incidents)
                    print(f'    📅 Weekend ratio: {weekend_ratio:.1%} (realistic if < 30%)')
    
    # 4. ORGANIZATIONAL STRUCTURE AUTHENTICITY
    print('\n🏢 ORGANIZATIONAL STRUCTURE:')
    if 'Assignment group' in df.columns:
        groups = df['Assignment group'].dropna().unique()
        print(f'  🏢 Assignment groups: {len(groups)}')
        
        # Check for enterprise naming patterns
        enterprise_patterns = ['AEDT', 'ADE', 'Enterprise', 'Tech', 'Spot']
        enterprise_groups = 0
        for group in groups:
            if any(pattern in str(group) for pattern in enterprise_patterns):
                enterprise_groups += 1
        
        print(f'  🏢 Enterprise naming: {enterprise_groups}/{len(groups)} ({enterprise_groups/len(groups)*100:.1f}%)')
        
        # Show sample groups
        print(f'  📝 Sample groups: {list(groups)[:3]}')
    
    # 5. GEOGRAPHIC DISTRIBUTION
    print('\n🌍 GEOGRAPHIC DISTRIBUTION:')
    location_columns = ['Location', 'Site', 'Region']
    for col in location_columns:
        if col in df.columns:
            locations = df[col].dropna().unique()
            print(f'  📍 {col}: {len(locations)} unique locations')
            if len(locations) <= 10:
                print(f'    Examples: {list(locations)[:5]}')
    
    # 6. BUSINESS METRICS REALISM
    print('\n📈 BUSINESS METRICS REALISM:')
    numeric_columns = ['Priority', 'Impact', 'Urgency']
    for col in numeric_columns:
        if col in df.columns:
            values = df[col].dropna()
            if len(values) > 0:
                print(f'  📊 {col}: Range {values.min()}-{values.max()}, Mean: {values.mean():.2f}')
    
    # 7. TIME DISTRIBUTION ANALYSIS
    print('\n⏰ TIME DISTRIBUTION ANALYSIS:')
    if 'Created' in df.columns:
        created_times = pd.to_datetime(df['Created'], errors='coerce').dropna()
        if len(created_times) > 0:
            hours = created_times.dt.hour
            hour_counts = hours.value_counts().sort_index()
            peak_hour = hour_counts.idxmax()
            peak_count = hour_counts.max()
            print(f'  ⏰ Peak hour: {peak_hour}:00 ({peak_count} incidents)')
            
            # Check for realistic business hours pattern
            business_hours = hour_counts[8:18].sum()
            total_hours = hour_counts.sum()
            business_ratio = business_hours / total_hours
            print(f'  🏢 Business hours (8-18): {business_ratio:.1%} of incidents')
            
            # Time variance (real data should have high variance)
            time_variance = hour_counts.var()
            print(f'  📊 Time distribution variance: {time_variance:.1f} (higher = more realistic)')
    
    # 8. FINAL AUTHENTICITY SCORING
    print('\n🎯 AUTHENTICITY ASSESSMENT:')
    authenticity_score = 0
    max_score = 0
    
    # INC format check
    if 'Number' in df.columns and valid_inc/len(incident_numbers) > 0.95:
        authenticity_score += 20
        print('  ✅ INC format: +20 points')
    max_score += 20
    
    # Low sequential pattern
    if 'Number' in df.columns and sequential_count/len(differences) < 0.05:
        authenticity_score += 20
        print('  ✅ Non-sequential incidents: +20 points')
    max_score += 20
    
    # No suspicious names
    if len(suspicious_names) == 0:
        authenticity_score += 20
        print('  ✅ No suspicious names: +20 points')
    max_score += 20
    
    # Realistic date range
    if 'Created' in df.columns and date_range.days > 30:
        authenticity_score += 20
        print('  ✅ Realistic date range: +20 points')
    max_score += 20
    
    # Enterprise structure
    if 'Assignment group' in df.columns and enterprise_groups/len(groups) > 0.5:
        authenticity_score += 20
        print('  ✅ Enterprise structure: +20 points')
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
    
    return final_score

# Run the analysis
if __name__ == "__main__":
    comprehensive_data_authenticity_analysis()
