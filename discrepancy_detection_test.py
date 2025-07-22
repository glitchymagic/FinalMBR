#!/usr/bin/env python3
"""
Comprehensive Discrepancy Detection Test Suite for MBR Dashboard - Incident Tab
Identifies data inconsistencies across all modules, drill-downs, and filter combinations
"""

import requests
import json
import time
from datetime import datetime
from collections import defaultdict

class DiscrepancyDetector:
    def __init__(self, base_url="http://127.0.0.1:3000"):
        self.base_url = base_url
        self.discrepancies = []
        self.passed_checks = []
        self.tolerance = 1  # Allow 1 unit difference for rounding
        
    def log_discrepancy(self, test_name, expected, actual, details=""):
        discrepancy = {
            'test_name': test_name,
            'expected': expected,
            'actual': actual,
            'difference': abs(expected - actual) if isinstance(expected, (int, float)) and isinstance(actual, (int, float)) else 'N/A',
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.discrepancies.append(discrepancy)
        print(f"❌ DISCREPANCY: {test_name}")
        print(f"   Expected: {expected}, Actual: {actual}")
        if details:
            print(f"   Details: {details}")
    
    def log_consistency(self, test_name, value, details=""):
        consistency = {
            'test_name': test_name,
            'value': value,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.passed_checks.append(consistency)
        print(f"✅ CONSISTENT: {test_name} = {value}")
        if details:
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
    
    def check_incident_count_consistency(self):
        """Check incident count consistency across all APIs"""
        print("\n🔍 CHECKING INCIDENT COUNT CONSISTENCY")
        print("-" * 60)
        
        # Get baseline from overview
        overview_data, error = self.make_request("/api/overview")
        if error:
            print(f"❌ Could not get overview data: {error}")
            return
        
        baseline_incidents = overview_data.get('total_incidents', 0)
        print(f"📊 BASELINE: {baseline_incidents} incidents from overview API")
        
        # Check team performance total
        teams_data, error = self.make_request("/api/team_performance")
        if not error and teams_data:
            team_total = sum([team.get('incidents', 0) for team in teams_data])
            if abs(baseline_incidents - team_total) <= self.tolerance:
                self.log_consistency("Team Performance Total", team_total, 
                                   f"Matches overview baseline ({baseline_incidents})")
            else:
                self.log_discrepancy("Team Performance Total", baseline_incidents, team_total,
                                   "Team performance total doesn't match overview")
        
        # Get SLA breach API data
        sla_data, error = self.make_request("/api/sla_breach")
        if not error and sla_data:
            api_breaches = sla_data.get('summary', {}).get('total_breaches', 0)
            sla_total_breaches = sla_data.get('total_breaches', 0)
            
            overview_breaches = overview_data.get('sla_breaches', 0)
            if abs(overview_breaches - api_breaches) <= self.tolerance:
                self.log_consistency("SLA Breach Count", api_breaches,
                                   f"Matches overview ({overview_breaches})")
            else:
                self.log_discrepancy("SLA Breach Count", overview_breaches, api_breaches,
                                   "SLA breach counts don't match between overview and SLA API")
        
        # Check technician count consistency
        overview_techs = overview_data.get('total_technicians', 0)
        techs_data, error = self.make_request("/api/technicians")
        if not error and techs_data:
            # Check data structure
            print(f"📊 Technicians API structure: {list(techs_data.keys()) if isinstance(techs_data, dict) else 'List/Other'}")
            
            if isinstance(techs_data, dict):
                # Use correct field names from the actual API
                api_techs = techs_data.get('total_technicians', 0)
                active_techs = techs_data.get('active_technicians', 0)
                regions = techs_data.get('regions', [])
                print(f"📊 API technicians: total={api_techs}, active={active_techs}, regions={len(regions)}")
                
                if abs(overview_techs - api_techs) <= self.tolerance:
                    self.log_consistency("Technician Count", api_techs,
                                       f"Matches overview ({overview_techs})")
                else:
                    self.log_discrepancy("Technician Count", overview_techs, api_techs,
                                       "Technician counts don't match between overview and technicians API")
            else:
                api_techs = len(techs_data) if isinstance(techs_data, list) else 0
                
                if abs(overview_techs - api_techs) <= self.tolerance:
                    self.log_consistency("Technician Count", api_techs,
                                       f"Matches overview ({overview_techs})")
                else:
                    self.log_discrepancy("Technician Count", overview_techs, api_techs,
                                       "Technician counts don't match between overview and technicians API")
        
        # Check location count consistency
        overview_locations = overview_data.get('total_locations', 0)
        locations_data, error = self.make_request("/api/locations")
        if not error and locations_data:
            if isinstance(locations_data, dict):
                actual_locations = len(locations_data.get('locations', []))
            else:
                actual_locations = len(locations_data) if isinstance(locations_data, list) else 0
            
            if abs(overview_locations - actual_locations) <= self.tolerance:
                self.log_consistency("Location Count", actual_locations,
                                   f"Matches overview ({overview_locations})")
            else:
                self.log_discrepancy("Location Count", overview_locations, actual_locations,
                                   "Location counts don't match between overview and locations API")
    
    def check_filter_consistency(self):
        """Check filter consistency across different APIs"""
        print("\n🔍 CHECKING FILTER CONSISTENCY")
        print("-" * 60)
        
        # Get filter options
        regions_data, _ = self.make_request("/api/regions")
        locations_data, _ = self.make_request("/api/locations")
        
        if not regions_data or not locations_data:
            print("❌ Could not get filter data")
            return
        
        regions = regions_data.get('regions', [])[:3]  # Test first 3
        locations = [l['value'] for l in locations_data.get('locations', [])][:3]  # Test first 3
        
        test_filters = [
            ('region', regions),
            ('location', locations),
            ('quarter', ['Q1', 'Q2']),
            ('month', ['2025-02', '2025-03'])
        ]
        
        for filter_type, values in test_filters:
            for value in values:
                params = {filter_type: value}
                filter_desc = f"{filter_type}={value}"
                
                # Get data from multiple APIs
                overview_data, _ = self.make_request("/api/overview", params)
                teams_data, _ = self.make_request("/api/team_performance", params)
                
                if overview_data and teams_data:
                    overview_incidents = overview_data.get('total_incidents', 0)
                    team_incidents = sum([team.get('incidents', 0) for team in teams_data])
                    
                    if abs(overview_incidents - team_incidents) <= self.tolerance:
                        self.log_consistency(f"Filter Consistency ({filter_desc})", overview_incidents,
                                           f"Overview and team performance match")
                    else:
                        self.log_discrepancy(f"Filter Consistency ({filter_desc})", 
                                           overview_incidents, team_incidents,
                                           "Overview and team performance don't match with filter")
    
    def check_drill_down_consistency(self):
        """Check drill-down data consistency"""
        print("\n🔍 CHECKING DRILL-DOWN CONSISTENCY")
        print("-" * 60)
        
        # Get team data for drill-down testing
        teams_data, error = self.make_request("/api/team_performance")
        if error or not teams_data:
            print("❌ Could not get team data")
            return
        
        # Test top 3 teams
        for team in teams_data[:3]:
            team_name = team.get('team', '')
            team_incidents = team.get('incidents', 0)
            
            if team_name:
                # Get drill-down data
                drill_data, error = self.make_request("/api/team_drill_down", {'team': team_name})
                
                if not error and drill_data:
                    drill_incidents = drill_data.get('total_incidents', 0)
                    
                    if abs(team_incidents - drill_incidents) <= self.tolerance:
                        self.log_consistency(f"Team Drill-down ({team_name})", drill_incidents,
                                           f"Matches team performance ({team_incidents})")
                    else:
                        self.log_discrepancy(f"Team Drill-down ({team_name})", 
                                           team_incidents, drill_incidents,
                                           "Team performance and drill-down incident counts don't match")
        
        # Check SLA breach drill-down consistency
        overview_data, _ = self.make_request("/api/overview")
        if overview_data:
            overview_breaches = overview_data.get('sla_breaches', 0)
            
            # Get breach data by severity
            severity_totals = 0
            for severity in ['minor', 'moderate', 'critical']:
                breach_data, error = self.make_request("/api/sla_breach_incidents", {'severity': severity})
                if not error and breach_data:
                    severity_count = len(breach_data.get('incidents', []))
                    severity_totals += severity_count
            
            if abs(overview_breaches - severity_totals) <= self.tolerance:
                self.log_consistency("SLA Breach Severity Totals", severity_totals,
                                   f"Matches overview total ({overview_breaches})")
            else:
                self.log_discrepancy("SLA Breach Severity Totals", overview_breaches, severity_totals,
                                   "Sum of severity breaches doesn't match overview total")
    
    def check_monthly_drill_down_consistency(self):
        """Check monthly drill-down data consistency"""
        print("\n🔍 CHECKING MONTHLY DRILL-DOWN CONSISTENCY")
        print("-" * 60)
        
        # Test monthly drill-downs with correct date format
        months = ['2025-02', '2025-03', '2025-04']
        
        for month in months:
            # Get overview data for the month
            overview_data, error = self.make_request("/api/overview", {'month': month})
            if error or not overview_data:
                continue
            
            month_incidents = overview_data.get('total_incidents', 0)
            month_fcr = overview_data.get('fcr_rate', 0)
            month_mttr = overview_data.get('avg_resolution_time', 0)
            
            # Check MTTR drill-down
            mttr_data, error = self.make_request("/api/mttr_drilldown", {'month': month})
            if not error and mttr_data:
                drill_mttr = mttr_data.get('summary', {}).get('avg_mttr_hours', 0)
                if abs(month_mttr - drill_mttr) <= 0.1:  # Allow 0.1 hour tolerance
                    self.log_consistency(f"MTTR Drill-down ({month})", drill_mttr,
                                       f"Matches overview MTTR ({month_mttr})")
                else:
                    self.log_discrepancy(f"MTTR Drill-down ({month})", month_mttr, drill_mttr,
                                       "MTTR values don't match between overview and drill-down")
            
            # Check FCR drill-down
            fcr_data, error = self.make_request("/api/fcr_drilldown", {'month': month})
            if not error and fcr_data:
                drill_fcr = fcr_data.get('fcr_rate', 0)
                if abs(month_fcr - drill_fcr) <= 0.1:  # Allow 0.1% tolerance
                    self.log_consistency(f"FCR Drill-down ({month})", drill_fcr,
                                       f"Matches overview FCR ({month_fcr})")
                else:
                    self.log_discrepancy(f"FCR Drill-down ({month})", month_fcr, drill_fcr,
                                       "FCR values don't match between overview and drill-down")
            
            # Check incident drill-down
            incident_data, error = self.make_request("/api/incident_drilldown", {'month': month})
            if not error and incident_data:
                drill_incidents = incident_data.get('total_incidents', 0)
                if abs(month_incidents - drill_incidents) <= self.tolerance:
                    self.log_consistency(f"Incident Drill-down ({month})", drill_incidents,
                                       f"Matches overview incidents ({month_incidents})")
                else:
                    self.log_discrepancy(f"Incident Drill-down ({month})", month_incidents, drill_incidents,
                                       "Incident counts don't match between overview and drill-down")
    
    def check_mathematical_consistency(self):
        """Check mathematical consistency in calculations"""
        print("\n🔍 CHECKING MATHEMATICAL CONSISTENCY")
        print("-" * 60)
        
        # Check region totals
        regions_data, error = self.make_request("/api/regions")
        if not error and regions_data:
            region_stats = regions_data.get('region_stats', [])
            total_from_regions = sum([r.get('incidents', 0) for r in region_stats])
            
            overview_data, _ = self.make_request("/api/overview")
            if overview_data:
                overview_total = overview_data.get('total_incidents', 0)
                
                if abs(total_from_regions - overview_total) <= self.tolerance:
                    self.log_consistency("Region Totals", total_from_regions,
                                       f"Sum of regions matches overview ({overview_total})")
                else:
                    self.log_discrepancy("Region Totals", overview_total, total_from_regions,
                                       "Sum of region incidents doesn't match overview total")
        
        # Check team totals
        teams_data, error = self.make_request("/api/team_performance")
        if not error and teams_data:
            team_total = sum([team.get('incidents', 0) for team in teams_data])
            
            overview_data, _ = self.make_request("/api/overview")
            if overview_data:
                overview_total = overview_data.get('total_incidents', 0)
                
                if abs(team_total - overview_total) <= self.tolerance:
                    self.log_consistency("Team Totals", team_total,
                                       f"Sum of teams matches overview ({overview_total})")
                else:
                    self.log_discrepancy("Team Totals", overview_total, team_total,
                                       "Sum of team incidents doesn't match overview total")
    
    def check_data_quality_consistency(self):
        """Check data quality and validation consistency"""
        print("\n🔍 CHECKING DATA QUALITY CONSISTENCY")
        print("-" * 60)
        
        # Check for impossible values
        overview_data, error = self.make_request("/api/overview")
        if not error and overview_data:
            fcr_rate = overview_data.get('fcr_rate', 0)
            if 0 <= fcr_rate <= 100:
                self.log_consistency("FCR Rate Range", fcr_rate, "Within valid range (0-100%)")
            else:
                self.log_discrepancy("FCR Rate Range", "0-100%", fcr_rate,
                                   "FCR rate outside valid percentage range")
            
            mttr = overview_data.get('avg_resolution_time', 0)
            if mttr >= 0:
                self.log_consistency("MTTR Value", mttr, "Non-negative value")
            else:
                self.log_discrepancy("MTTR Value", ">=0", mttr,
                                   "MTTR cannot be negative")
            
            sla_compliance = overview_data.get('sla_compliance', 0)
            if 0 <= sla_compliance <= 100:
                self.log_consistency("SLA Compliance Range", sla_compliance, "Within valid range (0-100%)")
            else:
                self.log_discrepancy("SLA Compliance Range", "0-100%", sla_compliance,
                                   "SLA compliance outside valid percentage range")
        
        # Check team performance data quality
        teams_data, error = self.make_request("/api/team_performance")
        if not error and teams_data:
            for team in teams_data:
                team_name = team.get('team', 'Unknown')
                team_fcr = team.get('fcr_rate', 0)
                team_incidents = team.get('incidents', 0)
                
                if team_incidents < 0:
                    self.log_discrepancy(f"Team Incidents ({team_name})", ">=0", team_incidents,
                                       "Team cannot have negative incidents")
                
                if not (0 <= team_fcr <= 100):
                    self.log_discrepancy(f"Team FCR ({team_name})", "0-100%", team_fcr,
                                       "Team FCR outside valid range")
    
    def run_discrepancy_detection(self):
        """Run all discrepancy detection tests"""
        print("🔍 COMPREHENSIVE DISCREPANCY DETECTION")
        print("=" * 60)
        print(f"Testing dashboard at: {self.base_url}")
        print("Checking for data inconsistencies across all modules...")
        print("=" * 60)
        
        # Wait for server
        time.sleep(2)
        
        # Run all discrepancy checks
        self.check_incident_count_consistency()
        self.check_filter_consistency()
        self.check_drill_down_consistency()
        self.check_monthly_drill_down_consistency()
        self.check_mathematical_consistency()
        self.check_data_quality_consistency()
        
        # Generate comprehensive report
        self.generate_discrepancy_report()
    
    def generate_discrepancy_report(self):
        """Generate comprehensive discrepancy report"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE DISCREPANCY DETECTION REPORT")
        print("=" * 60)
        
        total_checks = len(self.discrepancies) + len(self.passed_checks)
        discrepancy_count = len(self.discrepancies)
        consistency_count = len(self.passed_checks)
        accuracy_rate = (consistency_count / total_checks * 100) if total_checks > 0 else 0
        
        print(f"Total Checks Performed: {total_checks}")
        print(f"✅ Consistent: {consistency_count}")
        print(f"❌ Discrepancies Found: {discrepancy_count}")
        print(f"🎯 Data Accuracy Rate: {accuracy_rate:.1f}%")
        
        if discrepancy_count > 0:
            print(f"\n❌ DISCREPANCIES DETECTED ({discrepancy_count}):")
            print("-" * 50)
            for disc in self.discrepancies:
                print(f"• {disc['test_name']}")
                print(f"  Expected: {disc['expected']}, Actual: {disc['actual']}")
                if disc['details']:
                    print(f"  Issue: {disc['details']}")
                if disc['difference'] != 'N/A':
                    print(f"  Difference: {disc['difference']}")
                print()
        
        print(f"\n✅ CONSISTENT DATA POINTS ({consistency_count}):")
        print("-" * 50)
        for check in self.passed_checks:
            print(f"• {check['test_name']}: {check['value']}")
            if check['details']:
                print(f"  {check['details']}")
        
        print(f"\n📈 DATA QUALITY ASSESSMENT:")
        if accuracy_rate >= 95:
            print("🎉 EXCELLENT! Data is highly consistent with 95%+ accuracy")
            print("✅ Dashboard data integrity verified")
            print("✅ All critical calculations consistent")
            print("✅ Cross-API data alignment confirmed")
        elif accuracy_rate >= 85:
            print("✅ GOOD! Data is mostly consistent with minor discrepancies")
            print("⚠️  Some data points may need attention")
        else:
            print("⚠️  ATTENTION NEEDED! Significant data discrepancies found")
            print("🔧 Recommend investigating and fixing discrepancies")
        
        print(f"\n🔍 DISCREPANCY CATEGORIES:")
        categories = defaultdict(int)
        for disc in self.discrepancies:
            if 'Count' in disc['test_name']:
                categories['Count Mismatches'] += 1
            elif 'Filter' in disc['test_name']:
                categories['Filter Inconsistencies'] += 1
            elif 'Drill-down' in disc['test_name']:
                categories['Drill-down Discrepancies'] += 1
            elif 'Range' in disc['test_name'] or 'Value' in disc['test_name']:
                categories['Data Quality Issues'] += 1
            else:
                categories['Other Issues'] += 1
        
        for category, count in categories.items():
            print(f"• {category}: {count}")
        
        # Save detailed report
        report_file = f"discrepancy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'summary': {
                    'total_checks': total_checks,
                    'consistent': consistency_count,
                    'discrepancies': discrepancy_count,
                    'accuracy_rate': accuracy_rate,
                    'timestamp': datetime.now().isoformat()
                },
                'discrepancies': self.discrepancies,
                'consistent_checks': self.passed_checks,
                'categories': dict(categories)
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        print(f"🏁 DISCREPANCY DETECTION COMPLETED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    detector = DiscrepancyDetector()
    detector.run_discrepancy_detection()

if __name__ == "__main__":
    main()
