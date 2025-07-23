#!/usr/bin/env python3
import subprocess
import sys

def run_quick_test(description, url):
    """Run a quick curl test with timeout"""
    print(f"\n{description}:")
    print("-" * 30)
    try:
        result = subprocess.run(['curl', '-s', '--max-time', '3', url], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout:
            # Just check if we got valid JSON response
            if '"total_incidents"' in result.stdout or '"regions"' in result.stdout or '"teams"' in result.stdout:
                print("✅ API responded successfully")
                # Extract key numbers if possible
                if '"total_incidents":' in result.stdout:
                    import re
                    match = re.search(r'"total_incidents":(\d+)', result.stdout)
                    if match:
                        print(f"✅ Incidents: {match.group(1)}")
                return True
            else:
                print("⚠️  Got response but no expected data")
                return False
        else:
            print(f"❌ Failed: {result.stderr[:50] if result.stderr else 'No response'}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)[:50]}")
        return False

def main():
    print("🔍 QUICK INCIDENTS TAB TESTING")
    print("=" * 40)
    
    base_url = "http://127.0.0.1:3000"
    base_params = "?quarter=all&month=all&location=all&region=all&assignment_group=all"
    
    tests = [
        ("Overview API", f"{base_url}/api/overview{base_params}"),
        ("Technicians API", f"{base_url}/api/technicians{base_params}"),
        ("Team Performance", f"{base_url}/api/team_performance{base_params}"),
        ("SLA Breach API", f"{base_url}/api/sla_breach{base_params}"),
    ]
    
    results = []
    for desc, url in tests:
        success = run_quick_test(desc, url)
        results.append(success)
    
    print(f"\n📊 RESULTS:")
    print(f"✅ Successful tests: {sum(results)}/{len(results)}")
    
    if all(results):
        print("🎯 All APIs responding - filtering appears to be working!")
    else:
        print("⚠️  Some APIs had issues")

if __name__ == "__main__":
    main()
