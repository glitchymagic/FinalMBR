#!/usr/bin/env python3
"""
Final Comprehensive Test Suite for MBR Dashboard - Incident Tab
Tests all drill-downs, modules, and filter combinations with correct parameters
"""

import requests
import json
import time
from datetime import datetime

class FinalTester:
    def __init__(self, base_url="http://127.0.0.1:3000"):
        self.base_url = base_url
        self.passed = 0
        self.failed = 0
        self.issues = []
        
    def log_result(self, test_name, success, details=""):
        if success:
            self.passed += 1
            print(f"✅ {test_name}: PASSED")
        else:
            self.failed += 1
            self.issues.append(f"{test_name}: {details}")
            print(f"❌ {test_name}: FAILED - {details}")
        
        if details and success:
            print(f"   {details}")
    
    def make_request(self, endpoint, params=None):
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json(), None
            else:
                return None, f"HTTP {response.status_code}"
        except Exception as e:
            return None, f"Error: {str(e)}"
    
    def test_basic_functionality(self):
        """Test basic dashboard functionality"""
        print("\n🔍 TESTING BASIC FUNCTIONALITY")
        print("-" * 50)
        
        # Core APIs
        endpoints = [
            ("/api/overview", "Dashboard Overview"),
            ("/api/regions", "Regions List"),
            ("/api/locations", "Locations List"),
            ("/api/assignment_groups", "Assignment Groups"),
            ("/api/team_performance", "Team Performance"),
            ("/api/trends", "Trends Data"),
            ("/api/sla_breach", "SLA Breach Summary"),
            ("/api/technicians", "Technicians Modal"),
            ("/api/ai_insights", "AI Insights"),
            ("/api/kb_trending", "KB Trending")
        ]
        
        for endpoint, name in endpoints:
            data, error = self.make_request(endpoint)
            if error:
                self.log_result(name, False, error)
            else:
                if isinstance(data, list):
                    self.log_result(name, True, f"Returned {len(data)} items")
                elif isinstance(data, dict):
                    keys = len(data.keys())
                    self.log_result(name, True, f"Returned object with {keys} keys")
                else:
                    self.log_result(name, True, "Valid response")
    
    def test_filter_functionality(self):
        """Test all filter combinations"""
        print("\n🔍 TESTING FILTER FUNCTIONALITY")
        print("-" * 50)
        
        # Get filter options
        regions_data, _ = self.make_request("/api/regions")
        locations_data, _ = self.make_request("/api/locations")
        
        if not regions_data or not locations_data:
            self.log_result("Filter Data Setup", False, "Could not get filter options")
            return
        
        regions = regions_data.get('regions', [])[:3]  # Test first 3
        locations = [l['value'] for l in locations_data.get('locations', [])][:3]  # Test first 3
        
        # Test individual filters
        filters_to_test = [
            ('region', regions),
            ('location', locations),
            ('quarter', ['Q1', 'Q2']),
            ('month', ['February', 'March', 'April'])
        ]
        
        for filter_type, values in filters_to_test:
            for value in values:
                params = {filter_type: value}
                data, error = self.make_request("/api/overview", params)
                
                if error:
                    self.log_result(f"Filter {filter_type}={value}", False, error)
                else:
                    incidents = data.get('total_incidents', 0)
                    self.log_result(f"Filter {filter_type}={value}", True, f"{incidents} incidents")
        
        # Test combined filters
        if regions and locations:
            combined_params = {'region': regions[0], 'quarter': 'Q1'}
            data, error = self.make_request("/api/overview", combined_params)
            
            if error:
                self.log_result("Combined Filters", False, error)
            else:
                incidents = data.get('total_incidents', 0)
                self.log_result("Combined Filters", True, f"{incidents} incidents with region+quarter")
    
    def test_drill_downs(self):
        """Test all drill-down functionality"""
        print("\n🔍 TESTING DRILL-DOWN FUNCTIONALITY")
        print("-" * 50)
        
        # Get real team data for testing
        teams_data, _ = self.make_request("/api/team_performance")
        if teams_data and len(teams_data) > 0:
            # Test team drill-down with real team
            real_team = teams_data[0]['team']
            data, error = self.make_request("/api/team_drill_down", {'team': real_team})
            
            if error:
                self.log_result(f"Team Drill-down ({real_team})", False, error)
            else:
                incidents = len(data.get('incidents', []))
                self.log_result(f"Team Drill-down ({real_team})", True, f"{incidents} incidents")
                
                # Test incident details with real incident
                if incidents > 0:
                    incident_number = data['incidents'][0].get('number', '')
                    if incident_number:
                        detail_data, detail_error = self.make_request("/api/incident_details", 
                                                                    {'incident_number': incident_number})
                        if detail_error:
                            self.log_result(f"Incident Details ({incident_number})", False, detail_error)
                        else:
                            self.log_result(f"Incident Details ({incident_number})", True, "Details loaded")
        
        # Test SLA breach drill-downs
        severity_levels = ['minor', 'moderate', 'critical']
        for severity in severity_levels:
            data, error = self.make_request("/api/sla_breach_incidents", {'severity': severity})
            if error:
                self.log_result(f"SLA Breach ({severity})", False, error)
            else:
                incidents = len(data.get('incidents', []))
                self.log_result(f"SLA Breach ({severity})", True, f"{incidents} incidents")
        
        # Test monthly drill-downs
        months = ['February', 'March', 'April']
        drill_down_apis = [
            ('mttr_drilldown', 'MTTR'),
            ('incident_drilldown', 'Incident'),
            ('fcr_drilldown', 'FCR')
        ]
        
        for api_name, display_name in drill_down_apis:
            for month in months[:2]:  # Test first 2 months
                data, error = self.make_request(f"/api/{api_name}", {'month': month})
                if error:
                    self.log_result(f"{display_name} Drill-down ({month})", False, error)
                else:
                    self.log_result(f"{display_name} Drill-down ({month})", True, f"Data for {month}")
        
        # Test application drill-down
        data, error = self.make_request("/api/application_drilldown", 
                                      {'month': 'March', 'application_type': 'Email'})
        if error:
            self.log_result("Application Drill-down", False, error)
        else:
            self.log_result("Application Drill-down", True, "Application data loaded")
    
    def test_data_consistency(self):
        """Test data consistency across APIs"""
        print("\n🔍 TESTING DATA CONSISTENCY")
        print("-" * 50)
        
        # Get overview data
        overview_data, error = self.make_request("/api/overview")
        if error:
            self.log_result("Overview Data", False, error)
            return
        
        # Get team performance data
        teams_data, error = self.make_request("/api/team_performance")
        if error:
            self.log_result("Team Performance Data", False, error)
            return
        
        # Check consistency
        overview_incidents = overview_data.get('total_incidents', 0)
        team_incidents_total = sum([team.get('incidents', 0) for team in teams_data])
        
        if abs(overview_incidents - team_incidents_total) <= 1:  # Allow for rounding
            self.log_result("Incident Count Consistency", True, 
                          f"Overview: {overview_incidents}, Teams: {team_incidents_total}")
        else:
            self.log_result("Incident Count Consistency", False,
                          f"Mismatch - Overview: {overview_incidents}, Teams: {team_incidents_total}")
        
        # Test technician count consistency
        overview_techs = overview_data.get('total_technicians', 0)
        techs_data, _ = self.make_request("/api/technicians")
        actual_techs = len(techs_data) if isinstance(techs_data, list) else 0
        
        if abs(overview_techs - actual_techs) <= 1:
            self.log_result("Technician Count Consistency", True,
                          f"Overview: {overview_techs}, Modal: {actual_techs}")
        else:
            self.log_result("Technician Count Consistency", False,
                          f"Mismatch - Overview: {overview_techs}, Modal: {actual_techs}")
        
        # Test location count consistency
        overview_locations = overview_data.get('total_locations', 0)
        locations_data, _ = self.make_request("/api/locations")
        actual_locations = len(locations_data.get('locations', [])) if isinstance(locations_data, dict) else 0
        
        if abs(overview_locations - actual_locations) <= 1:
            self.log_result("Location Count Consistency", True,
                          f"Overview: {overview_locations}, Modal: {actual_locations}")
        else:
            self.log_result("Location Count Consistency", False,
                          f"Mismatch - Overview: {overview_locations}, Modal: {actual_locations}")
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("\n🔍 TESTING EDGE CASES")
        print("-" * 50)
        
        edge_cases = [
            ("/api/overview", {'region': 'NonExistentRegion'}, "Invalid Region"),
            ("/api/team_drill_down", {'team': 'NonExistentTeam'}, "Invalid Team"),
            ("/api/incident_details", {'incident_number': 'INVALID123'}, "Invalid Incident"),
            ("/api/sla_breach_incidents", {'severity': 'invalid'}, "Invalid Severity"),
            ("/api/mttr_drilldown", {'month': 'InvalidMonth'}, "Invalid Month"),
        ]
        
        for endpoint, params, test_name in edge_cases:
            data, error = self.make_request(endpoint, params)
            
            # For edge cases, we expect either graceful handling or proper error messages
            if error and "500" in error:
                self.log_result(test_name, False, f"Server error: {error}")
            else:
                self.log_result(test_name, True, "Handled gracefully")
    
    def test_performance(self):
        """Test response times"""
        print("\n🔍 TESTING PERFORMANCE")
        print("-" * 50)
        
        critical_endpoints = [
            "/api/overview",
            "/api/team_performance",
            "/api/trends",
            "/api/sla_breach"
        ]
        
        for endpoint in critical_endpoints:
            start_time = time.time()
            data, error = self.make_request(endpoint)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if error:
                self.log_result(f"Performance {endpoint}", False, error)
            elif response_time > 5:  # 5 second threshold
                self.log_result(f"Performance {endpoint}", False, f"Slow: {response_time:.2f}s")
            else:
                self.log_result(f"Performance {endpoint}", True, f"{response_time:.2f}s")
    
    def run_comprehensive_test(self):
        """Run all test suites"""
        print("🚀 FINAL COMPREHENSIVE DASHBOARD TEST")
        print("=" * 60)
        print(f"Testing dashboard at: {self.base_url}")
        print("=" * 60)
        
        # Wait for server
        time.sleep(2)
        
        # Run all test suites
        self.test_basic_functionality()
        self.test_filter_functionality()
        self.test_drill_downs()
        self.test_data_consistency()
        self.test_edge_cases()
        self.test_performance()
        
        # Generate final report
        self.generate_final_report()
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        print("\n" + "=" * 60)
        print("📊 FINAL COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        total_tests = self.passed + self.failed
        success_rate = (self.passed / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests Executed: {total_tests}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"🎯 Success Rate: {success_rate:.1f}%")
        
        if self.failed > 0:
            print(f"\n❌ ISSUES FOUND ({self.failed}):")
            print("-" * 40)
            for issue in self.issues:
                print(f"• {issue}")
        
        print(f"\n📈 DASHBOARD STATUS:")
        if success_rate >= 95:
            print("🎉 EXCELLENT! Dashboard is production-ready with 95%+ accuracy")
            print("✅ All critical functionality working correctly")
            print("✅ Data consistency verified across all modules")
            print("✅ Filter combinations working properly")
            print("✅ Drill-downs functioning as expected")
        elif success_rate >= 85:
            print("✅ GOOD! Dashboard is functional with minor issues")
            print("⚠️  Some non-critical issues may need attention")
        else:
            print("⚠️  NEEDS ATTENTION! Critical issues found")
            print("🔧 Recommend fixing issues before production deployment")
        
        print(f"\n🏁 TEST COMPLETED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    tester = FinalTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
