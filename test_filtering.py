#!/usr/bin/env python3
"""
Quick test script to verify non-technical resolver filtering
"""
import json
import urllib.request
import urllib.error
from urllib.parse import urlencode

def test_api(endpoint, params=None):
    """Test an API endpoint with timeout"""
    if params is None:
        params = {}
    
    url = f"http://127.0.0.1:3000{endpoint}"
    if params:
        url += "?" + urlencode(params)
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        return {"error": str(e)}

def main():
    print("🔍 INCIDENTS TAB FILTERING VERIFICATION")
    print("=" * 50)
    
    # Base parameters
    base_params = {
        'quarter': 'all',
        'month': 'all', 
        'location': 'all',
        'region': 'all',
        'assignment_group': 'all'
    }
    
    # Test 1: Overview API
    print("\n1. 📊 OVERVIEW API:")
    print("-" * 20)
    overview = test_api("/api/overview", base_params)
    if "error" not in overview:
        print(f"✅ Total Incidents: {overview['total_incidents']}")
        print(f"✅ Total Technicians: {overview['technicians']}")
        print(f"✅ Filtering Impact: {10342 - overview['total_incidents']} incidents removed")
        base_incidents = overview['total_incidents']
    else:
        print(f"❌ Error: {overview['error']}")
        return
    
    # Test 2: Technicians API
    print("\n2. 👥 TECHNICIANS API:")
    print("-" * 20)
    technicians = test_api("/api/technicians", base_params)
    if "error" not in technicians:
        total_techs = sum(len(region['technicians']) for region in technicians['regions'])
        total_incidents_from_techs = sum(tech['incidents'] for region in technicians['regions'] for tech in region['technicians'])
        print(f"✅ Technicians in modal: {total_techs}")
        print(f"✅ Total incidents from technicians: {total_incidents_from_techs}")
        print(f"✅ Consistency: {'MATCH' if base_incidents == total_incidents_from_techs else 'MISMATCH'}")
    else:
        print(f"❌ Error: {technicians['error']}")
    
    # Test 3: Team Performance API
    print("\n3. 🏢 TEAM PERFORMANCE API:")
    print("-" * 20)
    teams = test_api("/api/team_performance", base_params)
    if "error" not in teams:
        total_team_incidents = sum(team['incidents'] for team in teams['teams'])
        print(f"✅ Total incidents from teams: {total_team_incidents}")
        print(f"✅ Consistency: {'MATCH' if base_incidents == total_team_incidents else 'MISMATCH'}")
    else:
        print(f"❌ Error: {teams['error']}")
    
    # Test 4: SLA Breach API
    print("\n4. 🚨 SLA BREACH API:")
    print("-" * 20)
    sla = test_api("/api/sla_breach", base_params)
    if "error" not in sla:
        breach_incidents = sum(breach['incidents'] for breach in sla['breaches'])
        print(f"✅ SLA breach incidents: {breach_incidents}")
        print(f"✅ Breach teams: {len(sla['breaches'])}")
    else:
        print(f"❌ Error: {sla['error']}")
    
    print("\n✅ FILTERING VERIFICATION COMPLETE!")

if __name__ == "__main__":
    main()
