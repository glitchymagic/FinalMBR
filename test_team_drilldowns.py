#!/usr/bin/env python3
"""
Comprehensive Team Drill-Down Test
Tests all 24 team drill-downs to identify any failing teams
"""

import requests
import json
import sys

def test_all_team_drilldowns():
    """Test all team drill-downs to identify any issues"""
    
    print("🔍 COMPREHENSIVE TEAM DRILL-DOWN TEST")
    print("=" * 60)
    
    try:
        # Get all teams from team performance API
        print("📊 Fetching all teams from team performance API...")
        response = requests.get('http://localhost:3000/api/team_performance')
        if response.status_code != 200:
            print(f"❌ Failed to fetch team performance data: HTTP {response.status_code}")
            return False
        
        teams = response.json()
        print(f"✅ Found {len(teams)} teams to test")
        
        # Test each team drill-down
        successful_teams = []
        failed_teams = []
        
        for i, team in enumerate(teams, 1):
            team_name = team['team']
            incidents = team.get('incidents', 0)
            
            print(f"\n{i:2d}. Testing team: {team_name}")
            print(f"    Expected incidents: {incidents}")
            
            try:
                # Test team drill-down API
                drill_response = requests.get(f'http://localhost:3000/api/team_drill_down?team={team_name}')
                
                if drill_response.status_code == 200:
                    drill_data = drill_response.json()
                    
                    # Validate response structure
                    required_fields = ['team', 'total_incidents', 'incidents', 'metrics']
                    missing_fields = [field for field in required_fields if field not in drill_data]
                    
                    if missing_fields:
                        print(f"    ❌ Missing fields: {missing_fields}")
                        failed_teams.append({
                            'team': team_name,
                            'error': f'Missing fields: {missing_fields}',
                            'status': 'structure_error'
                        })
                    else:
                        drill_incidents = drill_data.get('total_incidents', 0)
                        print(f"    ✅ Drill-down incidents: {drill_incidents}")
                        
                        # Check for data consistency
                        if drill_incidents != incidents:
                            print(f"    ⚠️  Incident count mismatch: {incidents} vs {drill_incidents}")
                        
                        successful_teams.append({
                            'team': team_name,
                            'expected_incidents': incidents,
                            'drill_incidents': drill_incidents,
                            'consistent': drill_incidents == incidents
                        })
                        
                elif drill_response.status_code == 404:
                    print(f"    ❌ Team not found (404)")
                    failed_teams.append({
                        'team': team_name,
                        'error': 'Team not found (404)',
                        'status': 'not_found'
                    })
                else:
                    error_text = drill_response.text()[:100]
                    print(f"    ❌ HTTP {drill_response.status_code}: {error_text}")
                    failed_teams.append({
                        'team': team_name,
                        'error': f'HTTP {drill_response.status_code}: {error_text}',
                        'status': 'http_error'
                    })
                    
            except Exception as e:
                print(f"    ❌ Exception: {str(e)[:50]}")
                failed_teams.append({
                    'team': team_name,
                    'error': str(e)[:100],
                    'status': 'exception'
                })
        
        # Summary report
        print("\n" + "=" * 60)
        print("📊 TEAM DRILL-DOWN TEST SUMMARY")
        print("=" * 60)
        
        success_rate = len(successful_teams) / len(teams) * 100
        print(f"✅ Successful teams: {len(successful_teams)}/{len(teams)} ({success_rate:.1f}%)")
        print(f"❌ Failed teams: {len(failed_teams)}/{len(teams)}")
        
        if successful_teams:
            print(f"\n✅ SUCCESSFUL TEAMS ({len(successful_teams)}):")
            consistent_count = sum(1 for team in successful_teams if team['consistent'])
            print(f"   Data consistency: {consistent_count}/{len(successful_teams)} teams consistent")
            
            for team in successful_teams[:5]:  # Show first 5
                consistency = "✅" if team['consistent'] else "⚠️"
                print(f"   {consistency} {team['team']}: {team['drill_incidents']} incidents")
            
            if len(successful_teams) > 5:
                print(f"   ... and {len(successful_teams) - 5} more successful teams")
        
        if failed_teams:
            print(f"\n❌ FAILED TEAMS ({len(failed_teams)}):")
            for team in failed_teams:
                print(f"   ❌ {team['team']}: {team['error']}")
        
        # Frontend integration test
        print(f"\n🌐 FRONTEND INTEGRATION TEST:")
        print("Testing if frontend can access team drill-down functionality...")
        
        # Test a few teams with different parameters
        test_cases = [
            ('DGTC', 'all', 'all'),
            ('Homeoffice', '2025-02', 'all'),
            ('Sunnyvale', 'all', 'Q1')
        ]
        
        for team_name, month, quarter in test_cases:
            try:
                url = f'http://localhost:3000/api/team_drill_down?team={team_name}&month={month}&quarter={quarter}'
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ {team_name} (month={month}, quarter={quarter}): {data.get('total_incidents', 0)} incidents")
                else:
                    print(f"   ❌ {team_name} (month={month}, quarter={quarter}): HTTP {response.status_code}")
            except Exception as e:
                print(f"   ❌ {team_name} (month={month}, quarter={quarter}): {str(e)[:30]}")
        
        print(f"\n🎯 FINAL ASSESSMENT:")
        if success_rate >= 95:
            print("✅ EXCELLENT: Team drill-downs are working correctly")
            return True
        elif success_rate >= 80:
            print("⚠️  GOOD: Most team drill-downs working, some issues need attention")
            return True
        else:
            print("❌ POOR: Significant issues with team drill-downs")
            return False
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_all_team_drilldowns()
    sys.exit(0 if success else 1)
