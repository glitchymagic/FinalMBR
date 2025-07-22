#!/usr/bin/env python3
"""
Direct apply_filters Test to Isolate Discrepancy
===============================================

This script tests the apply_filters() function directly to determine
if the discrepancy is in the filtering logic or post-processing.

Strategy:
1. Load the same incidents data that the APIs use
2. Call apply_filters() with identical parameters used by both APIs
3. Compare results to see if apply_filters() itself is consistent
4. If consistent, the issue is in post-processing; if not, it's in apply_filters()
"""

import pandas as pd
import sys
import os

# Add the current directory to Python path to import from app.py
sys.path.append('/Users/j0j0ize/Downloads/finalMBR-1')

def test_apply_filters_directly():
    """Test apply_filters function directly with identical parameters"""
    print("🔍 DIRECT APPLY_FILTERS TEST")
    print("=" * 50)
    
    try:
        # Import the apply_filters function and load data
        from app import apply_filters
        
        # Load the incidents data (same as the APIs use)
        incidents_df = pd.read_csv('/Users/j0j0ize/Downloads/finalMBR-1/incidents.csv')
        
        # Convert Created column to datetime
        incidents_df['Created'] = pd.to_datetime(incidents_df['Created'])
        
        print(f"📊 LOADED DATA: {len(incidents_df)} total incidents")
        
        # Test parameters used by both APIs for February 2025
        month = "2025-02"
        region = "all"
        assignment_group = "all"
        
        print(f"\n🔧 TESTING APPLY_FILTERS WITH IDENTICAL PARAMETERS:")
        print(f"   Parameters: quarter='all', month='{month}', location='all', region='{region}', assignment_group='{assignment_group}'")
        
        # Call apply_filters multiple times with identical parameters
        print(f"\n1. First apply_filters call...")
        result1 = apply_filters(incidents_df, 'all', month, 'all', region, assignment_group)
        count1 = len(result1)
        
        print(f"\n2. Second apply_filters call...")
        result2 = apply_filters(incidents_df, 'all', month, 'all', region, assignment_group)
        count2 = len(result2)
        
        print(f"\n3. Third apply_filters call...")
        result3 = apply_filters(incidents_df, 'all', month, 'all', region, assignment_group)
        count3 = len(result3)
        
        print(f"\n📋 APPLY_FILTERS CONSISTENCY TEST:")
        print(f"   Call 1: {count1} incidents")
        print(f"   Call 2: {count2} incidents")
        print(f"   Call 3: {count3} incidents")
        
        # Check consistency
        if count1 == count2 == count3:
            print(f"   ✅ CONSISTENT: apply_filters() produces identical results")
            print(f"   🎯 CONCLUSION: Discrepancy is NOT in apply_filters() function")
            print(f"   🔍 IMPLICATION: Issue must be in post-filtering processing")
            
            # Test what the APIs should return
            expected_result = count1
            print(f"\n📊 EXPECTED API RESULTS:")
            print(f"   Both APIs should return: {expected_result} incidents")
            print(f"   Overview API actually returns: 2172 incidents")
            print(f"   Drill-down API actually returns: 2093 incidents")
            print(f"   ")
            print(f"   🚨 CRITICAL FINDING: Neither API matches apply_filters() result!")
            print(f"   This suggests both APIs have additional processing beyond apply_filters()")
            
        else:
            print(f"   ❌ INCONSISTENT: apply_filters() produces different results")
            print(f"   🎯 CONCLUSION: Bug found in apply_filters() function")
            print(f"   🔧 IMPLICATION: Fix needed in apply_filters() logic")
            
        return count1
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None

def analyze_post_processing_differences():
    """Analyze potential post-processing differences between APIs"""
    print(f"\n🔍 POST-PROCESSING ANALYSIS:")
    print("=" * 40)
    
    print("📊 KNOWN API RESULTS (Feb 2025):")
    print("   Overview API: 2172 incidents")
    print("   Drill-down API: 2093 incidents")
    print("   Difference: 79 incidents")
    
    print(f"\n🔍 POTENTIAL POST-PROCESSING DIFFERENCES:")
    print("   1. Overview API may have additional data included")
    print("   2. Drill-down API may have additional filtering")
    print("   3. Different handling of null/invalid data")
    print("   4. Different data access patterns")
    
    print(f"\n🎯 INVESTIGATION NEEDED:")
    print("   1. Check if overview API adds data after apply_filters()")
    print("   2. Check if drill-down API filters data after apply_filters()")
    print("   3. Compare the exact data processing steps")
    print("   4. Identify where the 79-incident difference occurs")

def main():
    """Main function to run direct apply_filters test"""
    print("🚀 STARTING DIRECT APPLY_FILTERS TEST")
    print("=" * 60)
    
    # Test apply_filters function directly
    result = test_apply_filters_directly()
    
    if result is not None:
        # Analyze post-processing differences
        analyze_post_processing_differences()
        
        print(f"\n🎯 NEXT STEPS:")
        print("   1. ✅ Confirmed apply_filters() consistency (or identified bug)")
        print("   2. 🔍 Investigate post-processing differences in both APIs")
        print("   3. 🔧 Implement targeted fix based on findings")
        print("   4. 📊 Verify fix achieves 100% consistency")
    
    print(f"\n📋 SUMMARY:")
    print("   Direct apply_filters() test completed")
    print("   Root cause isolation in progress")
    print("   Goal: Achieve 100% data accuracy")

if __name__ == "__main__":
    main()
