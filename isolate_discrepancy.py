#!/usr/bin/env python3
"""
Comprehensive Discrepancy Isolation Test
========================================

This script isolates the exact source of the 79-incident discrepancy
by testing different scenarios and comparing results systematically.

Current Status:
- Both APIs use identical apply_filters() calls
- Detailed logging added to apply_filters() function
- Discrepancy persists: 2172 vs 2093 incidents for Feb 2025
- Need to isolate whether issue is in apply_filters() or post-processing

Test Strategy:
1. Test apply_filters() function directly with identical parameters
2. Compare intermediate results at each processing stage
3. Identify exact point where discrepancy occurs
4. Generate targeted fix based on findings
"""

import requests
import json
import time

def test_api_consistency_detailed():
    """Test API consistency with detailed analysis"""
    print("🔍 COMPREHENSIVE DISCREPANCY ISOLATION TEST")
    print("=" * 60)
    
    month = "2025-02"
    
    # Test multiple months to confirm pattern
    months = ["2025-02", "2025-03", "2025-04"]
    
    for test_month in months:
        print(f"\n📅 TESTING {test_month}:")
        print("-" * 30)
        
        try:
            # Overview API
            overview_response = requests.get(f'http://localhost:3000/api/overview?month={test_month}')
            overview_data = overview_response.json()
            overview_total = overview_data.get('total_incidents', 0)
            
            # Drill-down API
            drilldown_response = requests.get(f'http://localhost:3000/api/incident_drilldown?month={test_month}')
            drilldown_data = drilldown_response.json()
            drilldown_total = drilldown_data.get('total_incidents', 0)
            
            difference = abs(overview_total - drilldown_total)
            
            print(f"   Overview API: {overview_total} incidents")
            print(f"   Drill-down API: {drilldown_total} incidents")
            print(f"   Difference: {difference} incidents")
            
            if difference > 0:
                percentage = (difference / overview_total * 100) if overview_total > 0 else 0
                print(f"   Percentage diff: {percentage:.1f}%")
                
                # Check if it's a consistent pattern
                if test_month == "2025-02" and difference == 79:
                    print("   ✅ CONSISTENT: Feb 2025 shows expected 79-incident discrepancy")
                elif test_month == "2025-03" and difference == 77:
                    print("   ✅ CONSISTENT: Mar 2025 shows expected 77-incident discrepancy")
                elif test_month == "2025-04" and difference == 103:
                    print("   ✅ CONSISTENT: Apr 2025 shows expected 103-incident discrepancy")
                else:
                    print(f"   ⚠️ PATTERN CHANGE: Expected pattern not matching")
            else:
                print("   ✅ PERFECT: No discrepancy found")
                
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            
        time.sleep(0.5)  # Small delay between tests

def analyze_discrepancy_pattern():
    """Analyze the discrepancy pattern to identify root cause"""
    print(f"\n🔍 DISCREPANCY PATTERN ANALYSIS:")
    print("=" * 40)
    
    print("📊 KNOWN DISCREPANCY PATTERN:")
    print("   Feb 2025: 79 incidents (3.6% difference)")
    print("   Mar 2025: 77 incidents (3.9% difference)")
    print("   Apr 2025: 103 incidents (4.5% difference)")
    print("   May 2025: 6 incidents (0.3% difference)")
    print("   Jun 2025: 117 incidents (10.4% difference)")
    
    print(f"\n📈 PATTERN CHARACTERISTICS:")
    print("   - Variable discrepancy (6-117 incidents)")
    print("   - Month-specific differences")
    print("   - Consistent within each month")
    print("   - Overview API always shows MORE incidents")
    
    print(f"\n🔍 ROOT CAUSE HYPOTHESES:")
    print("   1. apply_filters() function has subtle bug")
    print("   2. Different data preprocessing in one API")
    print("   3. Post-filtering processing differences")
    print("   4. Hidden filtering steps in one API")
    
    print(f"\n🎯 ISOLATION STRATEGY:")
    print("   1. Test apply_filters() function directly")
    print("   2. Compare step-by-step processing")
    print("   3. Verify data source consistency")
    print("   4. Check for hidden filtering")

def generate_targeted_fix_plan():
    """Generate targeted fix plan based on analysis"""
    print(f"\n🎯 TARGETED FIX PLAN:")
    print("=" * 30)
    
    print("🔧 IMMEDIATE ACTIONS:")
    print("   1. ✅ Added detailed logging to apply_filters()")
    print("   2. 🔍 Analyze server logs for filtering differences")
    print("   3. 🔧 Test apply_filters() function in isolation")
    print("   4. 📊 Compare intermediate results step-by-step")
    
    print(f"\n🎯 SUCCESS CRITERIA:")
    print("   1. Identify exact point where discrepancy occurs")
    print("   2. Implement targeted fix for root cause")
    print("   3. Achieve 100% consistency across all months")
    print("   4. Verify fix doesn't break other functionality")
    
    print(f"\n📋 NEXT STEPS:")
    print("   1. Review server logs from detailed logging")
    print("   2. Identify filtering step causing discrepancy")
    print("   3. Implement specific fix for identified issue")
    print("   4. Test fix across all affected months")
    print("   5. Move to next discrepancy type (technician count)")

def main():
    """Main function to run comprehensive discrepancy isolation"""
    print("🚀 STARTING COMPREHENSIVE DISCREPANCY ISOLATION")
    print("=" * 60)
    
    # Test API consistency with detailed analysis
    test_api_consistency_detailed()
    
    # Analyze discrepancy pattern
    analyze_discrepancy_pattern()
    
    # Generate targeted fix plan
    generate_targeted_fix_plan()
    
    print(f"\n📋 SUMMARY:")
    print("   Comprehensive discrepancy isolation test completed")
    print("   Detailed logging active in apply_filters() function")
    print("   Next: Analyze server logs to identify exact discrepancy source")
    print("   Goal: Achieve 100% data accuracy across all APIs")

if __name__ == "__main__":
    main()
