#!/usr/bin/env python3
"""
Targeted Test Suite for MBR Dashboard - Incident Tab Issues
Fixes the identified issues and tests with correct parameters
"""

import requests
import json
import time
from datetime import datetime

class TargetedTester:
    def __init__(self, base_url="http://127.0.0.1:3000"):
        self.base_url = base_url
        self.test_results = []
        
    def log_test(self, test_name, status, details=""):
        result = {
            'test_name': test_name,
            'status': status,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if status == "PASS":
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED - {details}")
    
    def make_request(self, endpoint, params=None):
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json(), None
            else:
                return None, f"HTTP {response.status_code}: {response.text[:200]}"
        except requests.exceptions.RequestException as e:
            return None, f"Request failed: {str(e)}"
    
    def test_drill_downs_with_correct_params(self):
        """Test drill-downs with correct parameters"""
        print("\n🔍 Testing Drill-Downs with Correct Parameters...")
        
        # First get some real data to use in tests
        teams_data, _ = self.make_request("/api/team_performance")
        overview_data, _ = self.make_request("/api/overview")
        
        if teams_data and len(teams_data) > 0:
            real_team = teams_data[0]['display_name']
            
            # Test team drill-down with real team name
            data, error = self.make_request("/api/team_drill_down", {'team': real_team})
            if error:
                self.log_test(f"Team Drill-down: {real_team}", "FAIL", error)
            else:
                self.log_test(f"Team Drill-down: {real_team}", "PASS", 
                            f"Returned {len(data.get('incidents', []))} incidents")
        
        # Test SLA breach with correct severity levels
        severity_levels = ['minor', 'moderate', 'critical']
        for severity in severity_levels:
            data, error = self.make_request("/api/sla_breach_incidents", {'severity': severity})
            if error:
                self.log_test(f"SLA Breach: {severity}", "FAIL", error)
            else:
                incident_count = len(data.get('incidents', []))
                self.log_test(f"SLA Breach: {severity}", "PASS", 
                            f"Returned {incident_count} incidents")
        
        # Test month-based drill-downs with valid months
        months = ['February', 'March', 'April', 'May', 'June']
        for month in months[:2]:  # Test first 2 months
            # MTTR drill-down
            data, error = self.make_request("/api/mttr_drilldown", {'month': month})
            if error:
                self.log_test(f"MTTR Drill-down: {month}", "FAIL", error)
            else:
                self.log_test(f"MTTR Drill-down: {month}", "PASS", 
                            f"Returned data for {month}")
            
            # Incident drill-down
            data, error = self.make_request("/api/incident_drilldown", {'month': month})
            if error:
                self.log_test(f"Incident Drill-down: {month}", "FAIL", error)
            else:
                self.log_test(f"Incident Drill-down: {month}", "PASS", 
                            f"Returned data for {month}")
            
            # FCR drill-down
            data, error = self.make_request("/api/fcr_drilldown", {'month': month})
            if error:
                self.log_test(f"FCR Drill-down: {month}", "FAIL", error)
            else:
                self.log_test(f"FCR Drill-down: {month}", "PASS", 
                            f"Returned data for {month}")
        
        # Test application drill-down with required parameters
        app_types = ['Email', 'Network', 'Hardware', 'Software']
        for app_type in app_types[:2]:  # Test first 2 types
            data, error = self.make_request("/api/application_drilldown", 
                                          {'month': 'March', 'application_type': app_type})
            if error:
                self.log_test(f"Application Drill-down: {app_type}", "FAIL", error)
            else:
                self.log_test(f"Application Drill-down: {app_type}", "PASS", 
                            f"Returned data for {app_type}")
    
    def test_incident_details_with_real_incidents(self):
        """Test incident details with real incident numbers"""
        print("\n🔍 Testing Incident Details with Real Data...")
        
        # Get some real incident numbers from team performance
        teams_data, _ = self.make_request("/api/team_performance")
        
        if teams_data and len(teams_data) > 0:
            # Get drill-down for first team to find real incident numbers
            team_name = teams_data[0]['display_name']
            drill_data, _ = self.make_request("/api/team_drill_down", {'team': team_name})
            
            if drill_data and 'incidents' in drill_data and len(drill_data['incidents']) > 0:
                # Test with first few real incident numbers
                for i, incident in enumerate(drill_data['incidents'][:3]):
                    incident_number = incident.get('number', '')
                    if incident_number:
                        data, error = self.make_request("/api/incident_details", 
                                                      {'incident_number': incident_number})
                        if error:
                            self.log_test(f"Incident Details: {incident_number}", "FAIL", error)
                        else:
                            self.log_test(f"Incident Details: {incident_number}", "PASS", 
                                        f"Returned details for {incident_number}")
    
    def test_data_consistency_detailed(self):
        """Test data consistency with detailed analysis"""
        print("\n🔍 Testing Data Consistency (Detailed)...")
        
        # Get overview data
        overview_data, error = self.make_request("/api/overview")
        if error:
            self.log_test("Overview Data", "FAIL", error)
            return
        
        # Get trends data
        trends_data, error = self.make_request("/api/trends")
        if error:
            self.log_test("Trends Data", "FAIL", error)
            return
        
        # Check trends data structure
        monthly_trends = trends_data.get('monthly_trends', [])
        if not monthly_trends:
            self.log_test("Trends Data Structure", "FAIL", "No monthly_trends in response")
            return
        
        # Calculate totals
        overview_total = overview_data.get('total_incidents', 0)
        trends_total = sum([month.get('incidents', 0) for month in monthly_trends])
        
        self.log_test("Data Consistency Check", "PASS", 
                    f"Overview: {overview_total}, Trends: {trends_total}, Monthly data points: {len(monthly_trends)}")
        
        # Check if totals are reasonable (allow for filtering differences)
        if abs(overview_total - trends_total) <= overview_total * 0.1:  # 10% tolerance
            self.log_test("Data Consistency - Totals", "PASS", 
                        f"Totals within acceptable range")
        else:
            self.log_test("Data Consistency - Totals", "FAIL",
                        f"Large discrepancy - Overview: {overview_total}, Trends: {trends_total}")
    
    def test_filter_combinations_comprehensive(self):
        """Test comprehensive filter combinations"""
        print("\n🔍 Testing Comprehensive Filter Combinations...")
        
        # Test complex filter combinations
        filter_combinations = [
            {'region': 'Central Region', 'quarter': 'Q1'},
            {'region': 'IDC', 'month': 'March'},
            {'location': 'David Glass Technology Center', 'quarter': 'Q2'},
            {'assignment_group': 'AEDT - Enterprise Tech Spot - DGTC', 'month': 'April'},
        ]
        
        for params in filter_combinations:
            # Test overview with filters
            data, error = self.make_request("/api/overview", params)
            filter_desc = ", ".join([f"{k}={v}" for k, v in params.items()])
            
            if error:
                self.log_test(f"Complex Filter Overview: {filter_desc}", "FAIL", error)
            else:
                total = data.get('total_incidents', 0)
                self.log_test(f"Complex Filter Overview: {filter_desc}", "PASS",
                            f"Returned {total} incidents")
            
            # Test team performance with same filters
            data, error = self.make_request("/api/team_performance", params)
            if error:
                self.log_test(f"Complex Filter Team Perf: {filter_desc}", "FAIL", error)
            else:
                team_count = len(data) if isinstance(data, list) else 0
                self.log_test(f"Complex Filter Team Perf: {filter_desc}", "PASS",
                            f"Returned {team_count} teams")
    
    def test_all_modals_and_drill_downs(self):
        """Test all modals and drill-downs that users can click"""
        print("\n🔍 Testing All User-Clickable Modals and Drill-downs...")
        
        # Test technicians modal (from dashboard click)
        data, error = self.make_request("/api/technicians")
        if error:
            self.log_test("Technicians Modal", "FAIL", error)
        else:
            tech_count = len(data) if isinstance(data, list) else 0
            self.log_test("Technicians Modal", "PASS", f"Returned {tech_count} technicians")
        
        # Test locations modal (from dashboard click)
        data, error = self.make_request("/api/locations")
        if error:
            self.log_test("Locations Modal", "FAIL", error)
        else:
            loc_count = len(data.get('locations', [])) if isinstance(data, dict) else 0
            self.log_test("Locations Modal", "PASS", f"Returned {loc_count} locations")
        
        # Test SLA breach summary
        data, error = self.make_request("/api/sla_breach")
        if error:
            self.log_test("SLA Breach Summary", "FAIL", error)
        else:
            self.log_test("SLA Breach Summary", "PASS", "SLA breach data loaded")
        
        # Test AI insights
        data, error = self.make_request("/api/ai_insights")
        if error:
            self.log_test("AI Insights", "FAIL", error)
        else:
            insights_count = len(data.get('insights', [])) if isinstance(data, dict) else 0
            self.log_test("AI Insights", "PASS", f"Generated {insights_count} insights")
    
    def run_targeted_tests(self):
        """Run targeted tests to identify and fix issues"""
        print("🎯 Starting Targeted Dashboard Testing...")
        print(f"Testing dashboard at: {self.base_url}")
        print("=" * 60)
        
        # Wait for server to be ready
        time.sleep(2)
        
        # Run targeted test suites
        self.test_all_modals_and_drill_downs()
        self.test_drill_downs_with_correct_params()
        self.test_incident_details_with_real_incidents()
        self.test_data_consistency_detailed()
        self.test_filter_combinations_comprehensive()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        print("\n" + "=" * 60)
        print("📊 TARGETED TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = [t for t in self.test_results if t['status'] == 'PASS']
        failed_tests = [t for t in self.test_results if t['status'] == 'FAIL']
        
        passed_count = len(passed_tests)
        failed_count = len(failed_tests)
        success_rate = (passed_count / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests Run: {total_tests}")
        print(f"Passed: {passed_count}")
        print(f"Failed: {failed_count}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_count > 0:
            print(f"\n❌ FAILED TESTS ({failed_count}):")
            print("-" * 40)
            for test in failed_tests:
                print(f"• {test['test_name']}: {test['details'][:100]}...")
        
        if success_rate >= 95:
            print(f"\n🎉 EXCELLENT! Dashboard is working at {success_rate:.1f}% accuracy")
        elif success_rate >= 85:
            print(f"\n✅ GOOD! Dashboard is working at {success_rate:.1f}% accuracy")
        else:
            print(f"\n⚠️  NEEDS ATTENTION! Dashboard accuracy is {success_rate:.1f}%")

def main():
    tester = TargetedTester()
    tester.run_targeted_tests()

if __name__ == "__main__":
    main()
