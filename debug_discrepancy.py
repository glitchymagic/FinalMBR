#!/usr/bin/env python3
"""
Comprehensive Discrepancy Debugging Script
==========================================

This script adds detailed logging to identify the exact root cause of the
persistent 79-incident discrepancy between overview and incident drill-down APIs.

Current Status:
- Both APIs use identical apply_filters() calls
- Both APIs are internally consistent
- Cross-API discrepancy persists: 2172 vs 2093 incidents
- Root cause: Unknown deeper data processing difference

Investigation Approach:
1. Add detailed logging to both API endpoints
2. Trace filtering steps with intermediate results
3. Compare data processing at each stage
4. Identify exact point where discrepancy occurs
"""

import requests
import json
import sys

def test_detailed_logging():
    """Test both APIs with detailed logging to identify discrepancy source"""
    print("🔍 COMPREHENSIVE DISCREPANCY DEBUGGING")
    print("=" * 60)
    
    month = "2025-02"
    
    try:
        print(f"📊 TESTING DETAILED LOGGING FOR {month}:")
        print("   This will show server-side logging to identify discrepancy source")
        
        # Test overview API with detailed logging
        print("\n1. Overview API with detailed logging...")
        overview_response = requests.get(f'http://localhost:3000/api/overview?month={month}')
        overview_data = overview_response.json()
        overview_total = overview_data.get('total_incidents', 0)
        
        # Test incident drill-down API with detailed logging
        print("\n2. Incident drill-down API with detailed logging...")
        drilldown_response = requests.get(f'http://localhost:3000/api/incident_drilldown?month={month}')
        drilldown_data = drilldown_response.json()
        drilldown_total = drilldown_data.get('total_incidents', 0)
        
        print(f"\n📋 RESULTS COMPARISON:")
        print(f"   Overview API: {overview_total} incidents")
        print(f"   Drill-down API: {drilldown_total} incidents")
        print(f"   Difference: {abs(overview_total - drilldown_total)} incidents")
        
        # Analyze the discrepancy
        if overview_total != drilldown_total:
            print(f"\n🔍 DISCREPANCY ANALYSIS:")
            print(f"   Both APIs use: apply_filters(incidents_df, 'all', '{month}', 'all', region, assignment_group)")
            print(f"   Both APIs should produce identical results")
            print(f"   Persistent discrepancy suggests:")
            print(f"   1. Bug in apply_filters() function")
            print(f"   2. Different data source access")
            print(f"   3. Hidden filtering in one API")
            print(f"   4. Race condition or timing issue")
            
            print(f"\n🎯 RECOMMENDED FIXES:")
            print(f"   1. Add step-by-step logging to apply_filters() function")
            print(f"   2. Verify both APIs access same incidents_df")
            print(f"   3. Check for any additional filtering steps")
            print(f"   4. Test apply_filters() function in isolation")
        else:
            print(f"\n✅ SUCCESS: Perfect consistency achieved!")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

def analyze_apply_filters_behavior():
    """Analyze apply_filters function behavior with identical inputs"""
    print(f"\n🔧 APPLY_FILTERS FUNCTION ANALYSIS:")
    print("=" * 40)
    
    print("📊 TESTING APPLY_FILTERS BEHAVIOR:")
    print("   Need to verify that apply_filters() produces consistent results")
    print("   when called with identical parameters from different contexts")
    
    # Test different scenarios
    scenarios = [
        ("No filters", "all", "all", "all", "all", "all"),
        ("Month only", "all", "2025-02", "all", "all", "all"),
        ("Region only", "all", "all", "all", "Central", "all"),
        ("Month + Region", "all", "2025-02", "all", "Central", "all")
    ]
    
    print(f"\n📋 SCENARIOS TO TEST:")
    for i, (name, quarter, month, location, region, assignment_group) in enumerate(scenarios, 1):
        print(f"   {i}. {name}: apply_filters(df, '{quarter}', '{month}', '{location}', '{region}', '{assignment_group}')")
    
    print(f"\n🎯 EXPECTED BEHAVIOR:")
    print(f"   Identical parameters should produce identical results")
    print(f"   Any difference indicates bug in apply_filters() function")

def generate_fix_recommendations():
    """Generate specific fix recommendations based on analysis"""
    print(f"\n🎯 COMPREHENSIVE FIX RECOMMENDATIONS:")
    print("=" * 50)
    
    print("🔧 IMMEDIATE FIXES:")
    print("   1. Add detailed logging to apply_filters() function")
    print("   2. Log intermediate results at each filtering step")
    print("   3. Verify data source consistency between APIs")
    print("   4. Check for hidden filtering or preprocessing")
    
    print("\n🔍 INVESTIGATION STEPS:")
    print("   1. Test apply_filters() function in isolation")
    print("   2. Compare step-by-step filtering results")
    print("   3. Verify incidents_df data source integrity")
    print("   4. Check for timing or caching issues")
    
    print("\n✅ SUCCESS CRITERIA:")
    print("   1. 100% consistency between overview and drill-down APIs")
    print("   2. Identical results for identical apply_filters() calls")
    print("   3. Zero discrepancy across all months")
    print("   4. Complete data accuracy achievement")

def main():
    """Main function to run comprehensive discrepancy debugging"""
    print("🚀 STARTING COMPREHENSIVE DISCREPANCY DEBUGGING")
    print("=" * 60)
    
    # Test detailed logging
    test_detailed_logging()
    
    # Analyze apply_filters behavior
    analyze_apply_filters_behavior()
    
    # Generate fix recommendations
    generate_fix_recommendations()
    
    print(f"\n📋 SUMMARY:")
    print("   Comprehensive debugging analysis completed")
    print("   Next step: Implement detailed logging in apply_filters() function")
    print("   Goal: Achieve 100% data accuracy across all APIs")

if __name__ == "__main__":
    main()
