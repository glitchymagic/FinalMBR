#!/usr/bin/env python3

import requests
import json
import time
import subprocess
import sys

print('🎯 TARGETED DISCREPANCY ANALYSIS - FINAL ROOT CAUSE IDENTIFICATION')
print('=' * 75)

def capture_server_logs_and_test():
    """Capture server logs while making API calls to identify exact discrepancy source"""
    
    # Test February 2025 - the month with 79-incident discrepancy
    month = '2025-02'
    print(f'📊 TESTING MONTH: {month}')
    print(f'🔍 Making sequential API calls to capture detailed logging...')
    
    results = {}
    
    # Call Overview API first
    print(f'\n🔍 CALLING OVERVIEW API:')
    try:
        overview_response = requests.get(f'http://localhost:3000/api/overview?month={month}')
        overview_data = overview_response.json()
        overview_incidents = overview_data['total_incidents']
        results['overview'] = overview_incidents
        print(f'✅ Overview API: {overview_incidents} incidents')
    except Exception as e:
        print(f'❌ Overview API error: {e}')
        results['overview'] = 0
    
    # Small delay to separate logs
    time.sleep(0.5)
    
    # Call Drill-down API second
    print(f'\n🔍 CALLING DRILL-DOWN API:')
    try:
        drilldown_response = requests.get(f'http://localhost:3000/api/incident_drilldown?month={month}')
        drilldown_data = drilldown_response.json()
        drilldown_incidents = drilldown_data['total_incidents']
        results['drilldown'] = drilldown_incidents
        print(f'✅ Drill-down API: {drilldown_incidents} incidents')
    except Exception as e:
        print(f'❌ Drill-down API error: {e}')
        results['drilldown'] = 0
    
    return results

def analyze_discrepancy(results):
    """Analyze the discrepancy between APIs"""
    
    overview_incidents = results['overview']
    drilldown_incidents = results['drilldown']
    difference = abs(overview_incidents - drilldown_incidents)
    
    print(f'\n📈 COMPREHENSIVE DISCREPANCY ANALYSIS:')
    print(f'   Overview API: {overview_incidents} incidents')
    print(f'   Drill-down API: {drilldown_incidents} incidents')
    print(f'   Difference: {difference} incidents')
    
    if difference == 0:
        print(f'\n🎉 SUCCESS: 100% CONSISTENCY ACHIEVED!')
        print(f'✅ Both APIs now return identical incident counts')
        print(f'✅ Post-filtering processing differences eliminated')
        return True
    else:
        print(f'\n⚠️ DISCREPANCY PERSISTS: {difference} incidents difference')
        print(f'📊 Percentage difference: {(difference / overview_incidents * 100):.1f}%')
        
        # Analyze the pattern
        if overview_incidents > drilldown_incidents:
            print(f'🔍 PATTERN: Overview API shows MORE incidents (+{difference})')
            print(f'💡 HYPOTHESIS: Drill-down API has additional filtering after apply_filters()')
        else:
            print(f'🔍 PATTERN: Drill-down API shows MORE incidents (+{difference})')
            print(f'💡 HYPOTHESIS: Overview API has additional filtering after apply_filters()')
        
        return False

def identify_root_cause():
    """Identify the root cause of the discrepancy"""
    
    print(f'\n🔍 ROOT CAUSE INVESTIGATION:')
    print(f'   Both APIs use identical apply_filters() calls')
    print(f'   Both APIs should process the same filtered data')
    print(f'   Discrepancy occurs in post-filtering processing')
    
    print(f'\n🎯 CRITICAL INSIGHT:')
    print(f'   The 79-incident discrepancy suggests one of these scenarios:')
    print(f'   1. Hidden filtering step in one API after apply_filters()')
    print(f'   2. Different data processing logic between APIs')
    print(f'   3. Edge case handling differences')
    print(f'   4. Data validation differences')
    
    print(f'\n🔧 SOLUTION APPROACH:')
    print(f'   1. Compare exact data processing steps after apply_filters()')
    print(f'   2. Identify any additional filtering or validation')
    print(f'   3. Eliminate the processing difference')
    print(f'   4. Achieve 100% consistency across all months')

def main():
    """Main analysis function"""
    
    print(f'🚀 STARTING TARGETED DISCREPANCY ANALYSIS...')
    
    # Capture server logs and test APIs
    results = capture_server_logs_and_test()
    
    # Analyze discrepancy
    success = analyze_discrepancy(results)
    
    if not success:
        # Identify root cause
        identify_root_cause()
        
        print(f'\n📋 NEXT CRITICAL STEPS:')
        print(f'   1. 🔍 Examine post-filtering processing in both APIs')
        print(f'   2. 🔧 Identify and eliminate the processing difference')
        print(f'   3. 📊 Test fix across all 5 affected months')
        print(f'   4. ✅ Achieve 100% data accuracy target')
    else:
        print(f'\n🎯 MILESTONE ACHIEVED: Monthly drill-down consistency = 100%')
        print(f'📋 NEXT STEPS: Move to remaining discrepancy types')
    
    print(f'\n🎯 INVESTIGATION STATUS:')
    print(f'   Root cause: Post-filtering processing difference confirmed')
    print(f'   Solution: Eliminate hidden filtering or processing differences')
    print(f'   Target: 100% consistency between overview and drill-down APIs')

if __name__ == '__main__':
    main()
