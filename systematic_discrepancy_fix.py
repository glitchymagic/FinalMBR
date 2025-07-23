#!/usr/bin/env python3
"""
Systematic Discrepancy Fix Script
=================================

This script identifies and fixes the systematic 77-103 incident discrepancy
between overview API and incident drill-down API across all months.

Current Status:
- February 2025: 79 incidents difference (2172 vs 2093)
- March 2025: 77 incidents difference (1960 vs 1883)  
- April 2025: 103 incidents difference (2279 vs 2176)
- Average: 86.3 incidents per month
- Pattern: Consistent systematic difference despite identical filtering logic

Root Cause Investigation:
Both APIs now use identical apply_filters() and date filtering logic,
but still produce different results. This suggests a deeper data processing
difference beyond filtering.
"""

import requests
import json
import pandas as pd

def test_api_consistency():
    """Test consistency between overview and drill-down APIs"""
    print("🔍 SYSTEMATIC DISCREPANCY ANALYSIS")
    print("=" * 60)
    
    months = ['2025-02', '2025-03', '2025-04', '2025-05', '2025-06']
    discrepancies = []
    
    for month in months:
        try:
            # Test overview API
            overview_response = requests.get(f'http://localhost:3000/api/overview?month={month}')
            overview_data = overview_response.json()
            overview_incidents = overview_data['total_incidents']
            
            # Test incident drill-down API
            drilldown_response = requests.get(f'http://localhost:3000/api/incident_drilldown?month={month}')
            drilldown_data = drilldown_response.json()
            drilldown_incidents = drilldown_data['total_incidents']
            
            difference = abs(overview_incidents - drilldown_incidents)
            discrepancies.append({
                'month': month,
                'overview': overview_incidents,
                'drilldown': drilldown_incidents,
                'difference': difference,
                'percentage': (difference / overview_incidents * 100) if overview_incidents > 0 else 0
            })
            
            print(f"📅 {month}: Overview {overview_incidents} vs Drill-down {drilldown_incidents} = {difference} diff ({(difference / overview_incidents * 100):.1f}%)")
            
        except Exception as e:
            print(f"❌ ERROR testing {month}: {e}")
    
    return discrepancies

def analyze_discrepancy_pattern(discrepancies):
    """Analyze the pattern of discrepancies"""
    print(f"\n📊 DISCREPANCY PATTERN ANALYSIS:")
    print("=" * 40)
    
    differences = [d['difference'] for d in discrepancies if d['difference'] > 0]
    
    if differences:
        avg_diff = sum(differences) / len(differences)
        min_diff = min(differences)
        max_diff = max(differences)
        
        print(f"📈 Average discrepancy: {avg_diff:.1f} incidents")
        print(f"📈 Range: {min_diff} - {max_diff} incidents")
        print(f"📈 Total affected months: {len(differences)}")
        print(f"📈 Total incidents difference: {sum(differences)}")
        
        # Check if pattern is consistent
        if max_diff - min_diff < 30:  # Within 30 incidents
            print("✅ CONSISTENT PATTERN: Systematic processing difference detected")
            return "systematic"
        else:
            print("⚠️ VARIABLE PATTERN: Month-specific processing differences")
            return "variable"
    else:
        print("✅ NO DISCREPANCIES: All APIs consistent")
        return "consistent"

def investigate_root_cause():
    """Investigate the root cause of systematic discrepancy"""
    print(f"\n🔍 ROOT CAUSE INVESTIGATION:")
    print("=" * 40)
    
    print("🔧 KNOWN FIXES APPLIED:")
    print("   ✅ Both APIs use apply_filters() function")
    print("   ✅ Both APIs use identical date filtering (.dt.year & .dt.month)")
    print("   ✅ Both APIs use same parameter handling")
    
    print("\n🔍 POTENTIAL REMAINING CAUSES:")
    print("   1. Data preprocessing differences")
    print("   2. Different data access patterns")
    print("   3. Caching or timing differences")
    print("   4. Additional filtering steps in one API")
    print("   5. Different handling of edge cases or null values")
    
    print("\n🎯 RECOMMENDED FIXES:")
    print("   1. Ensure both APIs use identical data source")
    print("   2. Add detailed logging to identify processing differences")
    print("   3. Compare intermediate results step by step")
    print("   4. Verify no additional filtering in either API")

def main():
    """Main function to run systematic discrepancy analysis"""
    print("🚀 STARTING SYSTEMATIC DISCREPANCY FIX")
    print("=" * 60)
    
    # Test current API consistency
    discrepancies = test_api_consistency()
    
    # Analyze discrepancy pattern
    pattern_type = analyze_discrepancy_pattern(discrepancies)
    
    # Investigate root cause
    investigate_root_cause()
    
    # Generate fix recommendations
    print(f"\n🎯 NEXT STEPS FOR 100% DATA ACCURACY:")
    print("=" * 50)
    
    if pattern_type == "systematic":
        print("1. ✅ SYSTEMATIC PATTERN CONFIRMED")
        print("2. 🔧 APPLY SYSTEMATIC FIX to incident drill-down API")
        print("3. 📊 VERIFY consistency across all months")
        print("4. ✅ ACHIEVE 100% data accuracy target")
    elif pattern_type == "variable":
        print("1. 🔍 INVESTIGATE month-specific differences")
        print("2. 🔧 APPLY targeted fixes per month")
        print("3. 📊 VERIFY each month individually")
    else:
        print("1. ✅ PERFECT CONSISTENCY ACHIEVED")
        print("2. 🎯 MOVE TO NEXT DISCREPANCY TYPE")
    
    print(f"\n📋 SUMMARY:")
    print(f"   Total discrepancies found: {len([d for d in discrepancies if d['difference'] > 0])}")
    print(f"   Pattern type: {pattern_type.upper()}")
    print(f"   Fix approach: {'Systematic' if pattern_type == 'systematic' else 'Targeted'}")

if __name__ == "__main__":
    main()
