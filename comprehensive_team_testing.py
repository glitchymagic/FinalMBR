#!/usr/bin/env python3
"""
COMPREHENSIVE TEAM DRILL-DOWN TESTING SCRIPT
============================================

This script systematically tests all 24 team drill-downs to identify:
1. Critical breaches data consistency issues
2. Other metric discrepancies (MTTR, FCR, incident counts)
3. Data accuracy across all team drill-down metrics

Goal: Achieve 100% data accuracy across all team drill-down data points
"""

import requests
import json
import pandas as pd
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:3000"
TEAMS_TO_TEST = [
    "DGTC", "Homeoffice", "Sunnyvale", "SD - Puerto Rico - Regional Office Tech Support",
    "Jst", "IDC Pardhanani", "IDC Building 10", "Hoboken", "IDC RMZ", "IDC Building 11",
    "IDC PTPP1", "San Bruno", "Sam's Club", "Hula", "Herndon", "Los Angeles",
    "Seattle", "Purpose", "I Street", "Charlotte", "MLK", "Ol'Roy", "Moonpie", "Aviation"
]

def get_team_performance_data():
    """Get main dashboard team performance data"""
    try:
        response = requests.get(f"{BASE_URL}/api/team_performance")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Team performance API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Team performance API exception: {e}")
        return None

def get_team_drill_down_data(team_name):
    """Get team drill-down data for specific team"""
    try:
        params = {
            'team': team_name,
            'quarter': 'all',
            'month': 'all'
        }
        response = requests.get(f"{BASE_URL}/api/team_drill_down", params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Team drill-down API error for {team_name}: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Team drill-down API exception for {team_name}: {e}")
        return None

def compare_team_metrics(team_name, main_data, drill_down_data):
    """Compare metrics between main dashboard and drill-down"""
    results = {
        'team': team_name,
        'incidents': {'status': 'unknown', 'main': 0, 'drill_down': 0, 'difference': 0},
        'critical_breaches': {'status': 'unknown', 'main': 0, 'drill_down': 0, 'difference': 0},
        'moderate_breaches': {'status': 'unknown', 'main': 0, 'drill_down': 0, 'difference': 0},
        'minor_breaches': {'status': 'unknown', 'main': 0, 'drill_down': 0, 'difference': 0},
        'mttr': {'status': 'unknown', 'main': 0.0, 'drill_down': 0.0, 'difference': 0.0},
        'fcr': {'status': 'unknown', 'main': 0.0, 'drill_down': 0.0, 'difference': 0.0},
        'sla_compliance': {'status': 'unknown', 'main': 0.0, 'drill_down': 0.0, 'difference': 0.0}
    }
    
    if not main_data or not drill_down_data:
        return results
    
    # Find team in main data
    team_main = None
    for team in main_data:
        if team.get('team') == team_name:
            team_main = team
            break
    
    if not team_main:
        print(f"⚠️  Team {team_name} not found in main data")
        return results
    
    # Extract drill-down metrics
    drill_metrics = drill_down_data.get('metrics', {})
    
    # Compare incidents
    main_incidents = team_main.get('incidents', 0)
    drill_incidents = drill_metrics.get('total_incidents', 0)
    results['incidents'] = {
        'status': 'match' if main_incidents == drill_incidents else 'mismatch',
        'main': main_incidents,
        'drill_down': drill_incidents,
        'difference': abs(main_incidents - drill_incidents)
    }
    
    # Compare critical breaches
    main_critical = team_main.get('critical_breaches', 0)
    drill_critical = drill_metrics.get('critical_breaches', 0)
    results['critical_breaches'] = {
        'status': 'match' if main_critical == drill_critical else 'mismatch',
        'main': main_critical,
        'drill_down': drill_critical,
        'difference': abs(main_critical - drill_critical)
    }
    
    # Compare moderate breaches
    main_moderate = team_main.get('moderate_breaches', 0)
    drill_moderate = drill_metrics.get('moderate_breaches', 0)
    results['moderate_breaches'] = {
        'status': 'match' if main_moderate == drill_moderate else 'mismatch',
        'main': main_moderate,
        'drill_down': drill_moderate,
        'difference': abs(main_moderate - drill_moderate)
    }
    
    # Compare minor breaches
    main_minor = team_main.get('minor_breaches', 0)
    drill_minor = drill_metrics.get('minor_breaches', 0)
    results['minor_breaches'] = {
        'status': 'match' if main_minor == drill_minor else 'mismatch',
        'main': main_minor,
        'drill_down': drill_minor,
        'difference': abs(main_minor - drill_minor)
    }
    
    # Compare MTTR
    main_mttr = team_main.get('avg_resolution_time', 0.0)
    drill_mttr = drill_metrics.get('avg_mttr_hours', 0.0)
    mttr_diff = abs(main_mttr - drill_mttr)
    results['mttr'] = {
        'status': 'match' if mttr_diff < 0.1 else 'mismatch',
        'main': main_mttr,
        'drill_down': drill_mttr,
        'difference': mttr_diff
    }
    
    # Compare FCR
    main_fcr = team_main.get('fcr_rate', 0.0)
    drill_fcr = drill_metrics.get('fcr_rate', 0.0)
    fcr_diff = abs(main_fcr - drill_fcr)
    results['fcr'] = {
        'status': 'match' if fcr_diff < 0.1 else 'mismatch',
        'main': main_fcr,
        'drill_down': drill_fcr,
        'difference': fcr_diff
    }
    
    # Compare SLA compliance
    main_sla = team_main.get('sla_goal_compliance', 0.0)
    drill_sla = drill_metrics.get('sla_compliance', 0.0)
    sla_diff = abs(main_sla - drill_sla)
    results['sla_compliance'] = {
        'status': 'match' if sla_diff < 0.1 else 'mismatch',
        'main': main_sla,
        'drill_down': drill_sla,
        'difference': sla_diff
    }
    
    return results

def run_comprehensive_team_testing():
    """Run comprehensive testing across all teams"""
    print("🚀 COMPREHENSIVE TEAM DRILL-DOWN TESTING")
    print("=" * 50)
    print(f"📅 Testing started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Testing {len(TEAMS_TO_TEST)} teams for data consistency")
    print()
    
    # Get main dashboard data
    print("📊 Fetching main dashboard team performance data...")
    main_data = get_team_performance_data()
    if not main_data:
        print("❌ Failed to get main dashboard data. Exiting.")
        return
    
    print(f"✅ Main dashboard data loaded: {len(main_data)} teams")
    print()
    
    # Test each team
    all_results = []
    successful_tests = 0
    total_mismatches = 0
    
    for i, team_name in enumerate(TEAMS_TO_TEST, 1):
        print(f"🔍 Testing team {i}/{len(TEAMS_TO_TEST)}: {team_name}")
        
        # Get drill-down data
        drill_down_data = get_team_drill_down_data(team_name)
        if not drill_down_data:
            print(f"❌ Failed to get drill-down data for {team_name}")
            continue
        
        # Compare metrics
        results = compare_team_metrics(team_name, main_data, drill_down_data)
        all_results.append(results)
        
        # Count mismatches for this team
        team_mismatches = sum(1 for metric in ['incidents', 'critical_breaches', 'moderate_breaches', 'minor_breaches', 'mttr', 'fcr', 'sla_compliance'] 
                             if results[metric]['status'] == 'mismatch')
        
        if team_mismatches == 0:
            print(f"✅ {team_name}: All metrics match perfectly")
            successful_tests += 1
        else:
            print(f"⚠️  {team_name}: {team_mismatches} metric mismatches found")
            total_mismatches += team_mismatches
            
            # Show specific mismatches
            for metric in ['incidents', 'critical_breaches', 'moderate_breaches', 'minor_breaches', 'mttr', 'fcr', 'sla_compliance']:
                if results[metric]['status'] == 'mismatch':
                    main_val = results[metric]['main']
                    drill_val = results[metric]['drill_down']
                    diff = results[metric]['difference']
                    print(f"   🔸 {metric}: {main_val} vs {drill_val} (diff: {diff})")
        
        print()
    
    # Generate summary report
    print("📋 COMPREHENSIVE TESTING SUMMARY")
    print("=" * 50)
    print(f"📊 Teams tested: {len(all_results)}/{len(TEAMS_TO_TEST)}")
    print(f"✅ Teams with perfect data consistency: {successful_tests}")
    print(f"⚠️  Teams with data mismatches: {len(all_results) - successful_tests}")
    print(f"🔢 Total metric mismatches found: {total_mismatches}")
    
    if len(all_results) > 0:
        success_rate = (successful_tests / len(all_results)) * 100
        print(f"📈 Data consistency success rate: {success_rate:.1f}%")
    
    print()
    
    # Detailed mismatch analysis
    if total_mismatches > 0:
        print("🔍 DETAILED MISMATCH ANALYSIS")
        print("=" * 30)
        
        mismatch_counts = {
            'incidents': 0, 'critical_breaches': 0, 'moderate_breaches': 0, 
            'minor_breaches': 0, 'mttr': 0, 'fcr': 0, 'sla_compliance': 0
        }
        
        for result in all_results:
            for metric in mismatch_counts.keys():
                if result[metric]['status'] == 'mismatch':
                    mismatch_counts[metric] += 1
        
        print("Metric mismatch frequency:")
        for metric, count in mismatch_counts.items():
            if count > 0:
                percentage = (count / len(all_results)) * 100
                print(f"  🔸 {metric}: {count} teams ({percentage:.1f}%)")
        
        print()
        
        # Show worst mismatches
        print("🚨 CRITICAL ISSUES REQUIRING IMMEDIATE ATTENTION:")
        critical_issues = []
        
        for result in all_results:
            team_name = result['team']
            
            # Check for significant critical breaches mismatches
            if result['critical_breaches']['status'] == 'mismatch' and result['critical_breaches']['difference'] > 10:
                critical_issues.append(f"Critical breaches: {team_name} ({result['critical_breaches']['main']} vs {result['critical_breaches']['drill_down']})")
            
            # Check for incident count mismatches
            if result['incidents']['status'] == 'mismatch' and result['incidents']['difference'] > 50:
                critical_issues.append(f"Incident count: {team_name} ({result['incidents']['main']} vs {result['incidents']['drill_down']})")
        
        if critical_issues:
            for issue in critical_issues:
                print(f"  🚨 {issue}")
        else:
            print("  ✅ No critical issues found - all mismatches are minor")
    
    print()
    print("🎯 NEXT STEPS:")
    if total_mismatches == 0:
        print("  ✅ Perfect data consistency achieved!")
        print("  🚀 Ready for production deployment")
    else:
        print("  🔧 Fix identified data consistency issues")
        print("  🔍 Investigate root causes of metric mismatches")
        print("  ✅ Re-run testing after fixes to verify 100% consistency")
    
    print()
    print(f"📅 Testing completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return all_results

if __name__ == "__main__":
    results = run_comprehensive_team_testing()
