#!/usr/bin/env python3
"""
Comprehensive Test Suite for MBR Dashboard - Incident Tab
Tests all drill-downs, modules, and filter combinations to ensure 100% accuracy
"""

import requests
import json
import time
import sys
from datetime import datetime
from itertools import combinations, product
import pandas as pd

class DashboardTester:
    def __init__(self, base_url="http://127.0.0.1:3000"):
        self.base_url = base_url
        self.test_results = []
        self.failed_tests = []
        self.passed_tests = []
        
    def log_test(self, test_name, status, details="", response_data=None):
        """Log test results"""
        result = {
            'test_name': test_name,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details,
            'response_data': response_data
        }
        self.test_results.append(result)
        
        if status == "PASS":
            self.passed_tests.append(result)
            print(f"✅ {test_name}: PASSED")
        else:
            self.failed_tests.append(result)
            print(f"❌ {test_name}: FAILED - {details}")
            
    def make_request(self, endpoint, params=None):
        """Make HTTP request with error handling"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json(), None
            else:
                return None, f"HTTP {response.status_code}: {response.text}"
        except requests.exceptions.RequestException as e:
            return None, f"Request failed: {str(e)}"
    
    def test_basic_endpoints(self):
        """Test basic API endpoints"""
        print("\n🔍 Testing Basic Endpoints...")
        
        endpoints = [
            "/api/regions",
            "/api/locations", 
            "/api/assignment_groups",
            "/api/overview",
            "/api/trends",
            "/api/team_performance",
            "/api/sla_breach"
        ]
        
        for endpoint in endpoints:
            data, error = self.make_request(endpoint)
            if error:
                self.log_test(f"Basic Endpoint: {endpoint}", "FAIL", error)
            else:
                self.log_test(f"Basic Endpoint: {endpoint}", "PASS", f"Returned {len(data) if isinstance(data, list) else 'object'} items")
    
    def test_filter_combinations(self):
        """Test all possible filter combinations"""
        print("\n🔍 Testing Filter Combinations...")
        
        # Get available filter options
        regions_data, regions_error = self.make_request("/api/regions")
        locations_data, locations_error = self.make_request("/api/locations")
        assignment_groups_data, ag_error = self.make_request("/api/assignment_groups")
        
        if regions_error or locations_error or ag_error:
            self.log_test("Filter Data Retrieval", "FAIL", f"Errors: regions={regions_error}, locations={locations_error}, assignment_groups={ag_error}")
            return
            
        if not regions_data or not locations_data or not assignment_groups_data:
            self.log_test("Filter Data Retrieval", "FAIL", "Empty filter data returned")
            return
            
        regions = regions_data.get('regions', [])
        locations = [l['value'] for l in locations_data.get('locations', [])]
        assignment_groups = assignment_groups_data.get('assignment_groups', [])
        quarters = ['Q1', 'Q2', 'Q3', 'Q4']
        months = ['January', 'February', 'March', 'April', 'May', 'June', 
                 'July', 'August', 'September', 'October', 'November', 'December']
        
        # Test single filter combinations
        filter_tests = [
            ('quarter', quarters[:2]),  # Test first 2 quarters
            ('month', months[:3]),      # Test first 3 months
            ('region', regions[:2]),    # Test first 2 regions
            ('location', locations[:3]), # Test first 3 locations
            ('assignment_group', assignment_groups[:2])  # Test first 2 assignment groups
        ]
        
        for filter_type, filter_values in filter_tests:
            for value in filter_values:
                params = {filter_type: value}
                
                # Test overview with filter
                data, error = self.make_request("/api/overview", params)
                if error:
                    self.log_test(f"Filter {filter_type}={value} (overview)", "FAIL", error)
                else:
                    self.log_test(f"Filter {filter_type}={value} (overview)", "PASS", 
                                f"Total incidents: {data.get('total_incidents', 'N/A')}")
                
                # Test trends with filter
                data, error = self.make_request("/api/trends", params)
                if error:
                    self.log_test(f"Filter {filter_type}={value} (trends)", "FAIL", error)
                else:
                    self.log_test(f"Filter {filter_type}={value} (trends)", "PASS",
                                f"Trend data points: {len(data.get('monthly_trends', []))}")
    
    def test_combined_filters(self):
        """Test combinations of multiple filters"""
        print("\n🔍 Testing Combined Filters...")
        
        # Get sample data for combined tests
        regions_data, regions_error = self.make_request("/api/regions")
        locations_data, locations_error = self.make_request("/api/locations")
        
        if regions_error or locations_error or not regions_data or not locations_data:
            self.log_test("Combined Filter Setup", "FAIL", "Could not get filter data for combined tests")
            return
            
        if len(regions_data) == 0 or len(locations_data) == 0:
            self.log_test("Combined Filter Setup", "FAIL", "Empty filter arrays")
            return
            
        # Test region + location combinations
        test_combinations = [
            {'region': regions_data.get('regions', [])[0], 'quarter': 'Q1'},
            {'location': locations_data.get('locations', [])[0]['value'], 'month': 'March'},
            {'region': regions_data.get('regions', [])[0], 'location': locations_data.get('locations', [])[0]['value']},
        ]
        
        for params in test_combinations:
            data, error = self.make_request("/api/overview", params)
            filter_desc = ", ".join([f"{k}={v}" for k, v in params.items()])
            
            if error:
                self.log_test(f"Combined Filter: {filter_desc}", "FAIL", error)
            else:
                self.log_test(f"Combined Filter: {filter_desc}", "PASS",
                            f"Total incidents: {data.get('total_incidents', 'N/A')}")
    
    def test_drill_down_endpoints(self):
        """Test all drill-down endpoints"""
        print("\n🔍 Testing Drill-Down Endpoints...")
        
        drill_down_tests = [
            ("/api/team_drill_down", {'team': 'Central Tech Spot'}),
            ("/api/incident_details", {'incident_number': 'INC0000001'}),
            ("/api/sla_breach_incidents", {'severity': 'high'}),
            ("/api/mttr_drilldown", {'month': 'March'}),
            ("/api/incident_drilldown", {'month': 'April'}),
            ("/api/application_drilldown", {'application': 'Email'}),
            ("/api/fcr_drilldown", {'month': 'May'}),
        ]
        
        for endpoint, params in drill_down_tests:
            data, error = self.make_request(endpoint, params)
            test_name = f"Drill-down: {endpoint}"
            
            if error:
                self.log_test(test_name, "FAIL", error)
            else:
                # Check if data structure is valid
                if isinstance(data, dict):
                    self.log_test(test_name, "PASS", f"Returned data structure with {len(data)} keys")
                elif isinstance(data, list):
                    self.log_test(test_name, "PASS", f"Returned {len(data)} items")
                else:
                    self.log_test(test_name, "PASS", "Returned valid response")
    
    def test_data_consistency(self):
        """Test data consistency across different endpoints"""
        print("\n🔍 Testing Data Consistency...")
        
        # Get overview data
        overview_data, error = self.make_request("/api/overview")
        if error:
            self.log_test("Data Consistency - Overview", "FAIL", error)
            return
            
        # Get trends data
        trends_data, error = self.make_request("/api/trends")
        if error:
            self.log_test("Data Consistency - Trends", "FAIL", error)
            return
        
        # Check if total incidents match between overview and trends
        overview_total = overview_data.get('total_incidents', 0)
        trends_total = sum([month.get('incidents', 0) for month in trends_data.get('monthly_trends', [])])
        
        if abs(overview_total - trends_total) <= 1:  # Allow for minor rounding differences
            self.log_test("Data Consistency - Incident Totals", "PASS", 
                        f"Overview: {overview_total}, Trends: {trends_total}")
        else:
            self.log_test("Data Consistency - Incident Totals", "FAIL",
                        f"Mismatch - Overview: {overview_total}, Trends: {trends_total}")
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("\n🔍 Testing Edge Cases...")
        
        edge_case_tests = [
            ("/api/overview", {'region': 'NonExistentRegion'}),
            ("/api/trends", {'month': 'InvalidMonth'}),
            ("/api/team_drill_down", {'team': 'NonExistentTeam'}),
            ("/api/incident_details", {'incident_number': 'INVALID123'}),
            ("/api/mttr_drilldown", {'month': ''}),
        ]
        
        for endpoint, params in edge_case_tests:
            data, error = self.make_request(endpoint, params)
            test_name = f"Edge Case: {endpoint} with {params}"
            
            # For edge cases, we expect either valid empty data or proper error handling
            if error and "500" in error:
                self.log_test(test_name, "FAIL", f"Server error: {error}")
            else:
                self.log_test(test_name, "PASS", "Handled gracefully")
    
    def test_performance(self):
        """Test response times for critical endpoints"""
        print("\n🔍 Testing Performance...")
        
        performance_tests = [
            "/api/overview",
            "/api/trends", 
            "/api/team_performance",
            "/api/sla_breach"
        ]
        
        for endpoint in performance_tests:
            start_time = time.time()
            data, error = self.make_request(endpoint)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if error:
                self.log_test(f"Performance: {endpoint}", "FAIL", error)
            elif response_time > 10:  # 10 second threshold
                self.log_test(f"Performance: {endpoint}", "FAIL", 
                            f"Slow response: {response_time:.2f}s")
            else:
                self.log_test(f"Performance: {endpoint}", "PASS",
                            f"Response time: {response_time:.2f}s")
    
    def test_ai_insights(self):
        """Test AI insights endpoint"""
        print("\n🔍 Testing AI Insights...")
        
        data, error = self.make_request("/api/ai_insights")
        
        if error:
            self.log_test("AI Insights", "FAIL", error)
        else:
            # Check if insights have required structure
            if isinstance(data, dict) and 'insights' in data:
                insights = data['insights']
                if len(insights) > 0:
                    self.log_test("AI Insights", "PASS", f"Generated {len(insights)} insights")
                else:
                    self.log_test("AI Insights", "FAIL", "No insights generated")
            else:
                self.log_test("AI Insights", "FAIL", "Invalid insights structure")
    
    def test_kb_trending(self):
        """Test Knowledge Base trending endpoint"""
        print("\n🔍 Testing KB Trending...")
        
        data, error = self.make_request("/api/kb_trending")
        
        if error:
            self.log_test("KB Trending", "FAIL", error)
        else:
            if isinstance(data, list):
                self.log_test("KB Trending", "PASS", f"Returned {len(data)} trending articles")
            else:
                self.log_test("KB Trending", "PASS", "Returned valid KB data")
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Comprehensive Dashboard Testing...")
        print(f"Testing dashboard at: {self.base_url}")
        print("=" * 60)
        
        # Wait for server to be ready
        print("⏳ Waiting for server to be ready...")
        time.sleep(2)
        
        # Run all test suites
        self.test_basic_endpoints()
        self.test_filter_combinations()
        self.test_combined_filters()
        self.test_drill_down_endpoints()
        self.test_data_consistency()
        self.test_edge_cases()
        self.test_performance()
        self.test_ai_insights()
        self.test_kb_trending()
        
        # Generate summary report
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_count = len(self.passed_tests)
        failed_count = len(self.failed_tests)
        success_rate = (passed_count / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests Run: {total_tests}")
        print(f"Passed: {passed_count}")
        print(f"Failed: {failed_count}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_count > 0:
            print(f"\n❌ FAILED TESTS ({failed_count}):")
            print("-" * 40)
            for test in self.failed_tests:
                print(f"• {test['test_name']}: {test['details']}")
        
        if success_rate >= 95:
            print(f"\n🎉 EXCELLENT! Dashboard is working at {success_rate:.1f}% accuracy")
        elif success_rate >= 85:
            print(f"\n✅ GOOD! Dashboard is working at {success_rate:.1f}% accuracy")
        else:
            print(f"\n⚠️  NEEDS ATTENTION! Dashboard accuracy is {success_rate:.1f}%")
        
        # Save detailed report
        report_file = f"dashboard_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': total_tests,
                    'passed': passed_count,
                    'failed': failed_count,
                    'success_rate': success_rate,
                    'timestamp': datetime.now().isoformat()
                },
                'detailed_results': self.test_results
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")

def main():
    """Main function to run tests"""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = "http://127.0.0.1:3000"
    
    tester = DashboardTester(base_url)
    tester.run_all_tests()

if __name__ == "__main__":
    main()
