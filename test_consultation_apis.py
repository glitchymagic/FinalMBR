#!/usr/bin/env python3
import requests
import json

def test_consultation_api(endpoint, description):
    """Test a consultation API endpoint"""
    print(f"\n{description}:")
    print("-" * 40)
    try:
        url = f"http://127.0.0.1:3000{endpoint}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if 'error' in data:
                print(f"❌ API Error: {data['error']}")
                return False
            else:
                print("✅ API Success")
                
                # Extract key metrics based on endpoint
                if 'overview' in endpoint:
                    print(f"📊 Total Consultations: {data.get('total_consultations', 0):,}")
                    print(f"✅ Completion Rate: {data.get('completion_rate', 0)}%")
                    print(f"🎫 INC Creation Rate: {data.get('inc_creation_rate', 0)}%")
                    types = data.get('consultation_type_breakdown', {})
                    print(f"📋 Consultation Types: {len(types)} types")
                
                elif 'locations' in endpoint:
                    locations = data.get('locations', [])
                    print(f"📍 Total Locations: {len(locations)}")
                    if locations:
                        top_location = max(locations, key=lambda x: x['consultation_count'])
                        print(f"🏆 Top Location: {top_location['display_name']} ({top_location['consultation_count']:,} consultations)")
                
                elif 'regions' in endpoint:
                    regions = data.get('regions', [])
                    print(f"🌍 Total Regions: {len(regions)}")
                    if regions:
                        top_region = max(regions, key=lambda x: x['consultation_count'])
                        print(f"🏆 Top Region: {top_region['display_name']} ({top_region['consultation_count']:,} consultations)")
                
                return True
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Request Error: {str(e)[:50]}")
        return False

def main():
    print("🧪 COMPREHENSIVE CONSULTATION API TESTING")
    print("=" * 50)
    
    # Test key consultation APIs
    tests = [
        ("/api/consultations/overview?quarter=all&location=all&region=all", "Consultation Overview API"),
        ("/api/consultations/locations", "Consultation Locations API"),
        ("/api/consultations/regions", "Consultation Regions API"),
    ]
    
    results = []
    for endpoint, description in tests:
        success = test_consultation_api(endpoint, description)
        results.append(success)
    
    print(f"\n📊 FINAL RESULTS:")
    print("=" * 30)
    print(f"✅ Successful APIs: {sum(results)}/{len(results)}")
    print(f"📈 Success Rate: {(sum(results)/len(results))*100:.1f}%")
    
    if all(results):
        print("\n🎉 ALL CONSULTATION APIs WORKING PERFECTLY!")
        print("🚀 Consultation dashboard ready for testing!")
    else:
        print(f"\n⚠️  {len(results) - sum(results)} APIs need attention")

if __name__ == "__main__":
    main()
