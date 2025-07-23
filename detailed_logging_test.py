#!/usr/bin/env python3

import requests
import json

print('🎯 DETAILED LOGGING TEST - IDENTIFYING EXACT DISCREPANCY SOURCE')
print('=' * 70)

# Test February 2025 - the month with 79-incident discrepancy
month = '2025-02'
print(f'📊 TESTING MONTH: {month}')
print(f'Expected discrepancy: Overview API shows ~79 more incidents than drill-down API')

print(f'\n🔍 CALLING OVERVIEW API:')
try:
    overview_response = requests.get(f'http://localhost:3000/api/overview?month={month}')
    overview_data = overview_response.json()
    overview_incidents = overview_data['total_incidents']
    print(f'✅ Overview API response: {overview_incidents} incidents')
except Exception as e:
    print(f'❌ Overview API error: {e}')
    overview_incidents = 0

print(f'\n🔍 CALLING DRILL-DOWN API:')
try:
    drilldown_response = requests.get(f'http://localhost:3000/api/incident_drilldown?month={month}')
    drilldown_data = drilldown_response.json()
    drilldown_incidents = drilldown_data['total_incidents']
    print(f'✅ Drill-down API response: {drilldown_incidents} incidents')
except Exception as e:
    print(f'❌ Drill-down API error: {e}')
    drilldown_incidents = 0

print(f'\n📈 DISCREPANCY ANALYSIS:')
difference = abs(overview_incidents - drilldown_incidents)
print(f'   Overview API: {overview_incidents} incidents')
print(f'   Drill-down API: {drilldown_incidents} incidents')
print(f'   Difference: {difference} incidents')

if difference == 0:
    print(f'\n🎉 SUCCESS: 100% CONSISTENCY ACHIEVED!')
    print(f'✅ Both APIs now return identical incident counts')
    print(f'✅ Post-filtering processing differences eliminated')
else:
    print(f'\n⚠️ DISCREPANCY PERSISTS: {difference} incidents difference')
    print(f'📊 Percentage difference: {(difference / overview_incidents * 100):.1f}%')
    print(f'🔍 Check server logs above for detailed apply_filters() tracing')
    print(f'💡 The logging should reveal where the {difference}-incident difference occurs')

print(f'\n🎯 NEXT STEPS:')
if difference == 0:
    print(f'   1. ✅ Monthly drill-down consistency achieved')
    print(f'   2. 🔄 Test all 5 months to verify complete fix')
    print(f'   3. 🎯 Move to next discrepancy type (technician count)')
else:
    print(f'   1. 🔍 Analyze server logs to identify exact filtering difference')
    print(f'   2. 🔧 Implement targeted fix based on log analysis')
    print(f'   3. 📊 Re-test to verify 100% consistency')
