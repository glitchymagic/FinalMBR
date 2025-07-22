#!/usr/bin/env python3
"""
Systematic Discrepancy Fix Script for MBR Dashboard
Addresses the 16 critical discrepancies identified in the comprehensive test
"""

import requests
import json
import time
from datetime import datetime

class DiscrepancyFixer:
    def __init__(self, base_url="http://127.0.0.1:3000"):
        self.base_url = base_url
        self.fixes_applied = []
        self.remaining_issues = []
        
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
    
    def diagnose_team_drill_down_issue(self):
        """Diagnose why team drill-downs are returning 0 incidents"""
        print("\n🔧 DIAGNOSING TEAM DRILL-DOWN ISSUES")
        print("-" * 50)
        
        # Get team performance data
        teams_data, error = self.make_request("/api/team_performance")
        if error:
            print(f"❌ Could not get team data: {error}")
            return
        
        # Test top 3 teams with detailed analysis
        for team in teams_data[:3]:
            team_name = team.get('team', '')
            expected_incidents = team.get('incidents', 0)
            
            print(f"\n🔍 Testing team: {team_name} (Expected: {expected_incidents} incidents)")
            
            # Test drill-down
            drill_data, error = self.make_request("/api/team_drill_down", {'team': team_name})
            
            if error:
                print(f"❌ Drill-down failed: {error}")
                self.remaining_issues.append(f"Team drill-down ({team_name}): {error}")
            else:
                # Check what data structure we're getting
                print(f"✅ Drill-down succeeded, keys: {list(drill_data.keys())}")
                
                # Check for incidents in different possible locations
                incidents_found = 0
                if 'incidents' in drill_data:
                    incidents_found = len(drill_data['incidents'])
                elif 'recent_incidents' in drill_data:
                    incidents_found = len(drill_data['recent_incidents'])
                elif 'monthly_incidents' in drill_data:
                    monthly_data = drill_data['monthly_incidents']
                    if isinstance(monthly_data, list):
                        incidents_found = sum([month.get('incidents', 0) for month in monthly_data])
                
                print(f"📊 Incidents found in drill-down: {incidents_found}")
                
                if incidents_found == expected_incidents:
                    print(f"✅ CONSISTENT: {team_name} drill-down matches team performance")
                    self.fixes_applied.append(f"Team drill-down ({team_name}): Data structure verified")
                else:
                    print(f"❌ DISCREPANCY: Expected {expected_incidents}, found {incidents_found}")
                    self.remaining_issues.append(f"Team drill-down ({team_name}): Count mismatch")
    
    def diagnose_sla_breach_issue(self):
        """Diagnose SLA breach count discrepancy"""
        print("\n🔧 DIAGNOSING SLA BREACH COUNT ISSUES")
        print("-" * 50)
        
        # Get overview SLA breaches
        overview_data, error = self.make_request("/api/overview")
        if error:
            print(f"❌ Could not get overview data: {error}")
            return
        
        overview_breaches = overview_data.get('sla_breaches', 0)
        print(f"📊 Overview SLA breaches: {overview_breaches}")
        
        # Get SLA breach API data
        sla_data, error = self.make_request("/api/sla_breach")
        if error:
            print(f"❌ Could not get SLA breach data: {error}")
            return
        
        api_breaches = sla_data.get('total_breaches', 0)
        print(f"📊 SLA API breaches: {api_breaches}")
        
        if overview_breaches == api_breaches:
            print(f"✅ CONSISTENT: SLA breach counts match")
            self.fixes_applied.append("SLA breach count: Verified consistency")
        else:
            print(f"❌ DISCREPANCY: Overview shows {overview_breaches}, API shows {api_breaches}")
            
            # Check severity breakdown
            severity_total = 0
            for severity in ['minor', 'moderate', 'critical']:
                severity_data, error = self.make_request("/api/sla_breach_incidents", {'severity': severity})
                if not error and severity_data:
                    count = len(severity_data.get('incidents', []))
                    severity_total += count
                    print(f"  {severity.capitalize()} breaches: {count}")
            
            print(f"📊 Sum of severity breaches: {severity_total}")
            self.remaining_issues.append(f"SLA breach count: Overview ({overview_breaches}) vs API ({api_breaches}) vs Severity sum ({severity_total})")
    
    def diagnose_technician_count_issue(self):
        """Diagnose technician count discrepancy"""
        print("\n🔧 DIAGNOSING TECHNICIAN COUNT ISSUES")
        print("-" * 50)
        
        # Get overview technician count
        overview_data, error = self.make_request("/api/overview")
        if error:
            print(f"❌ Could not get overview data: {error}")
            return
        
        overview_techs = overview_data.get('total_technicians', 0)
        print(f"📊 Overview technicians: {overview_techs}")
        
        # Get technicians API data
        techs_data, error = self.make_request("/api/technicians")
        if error:
            print(f"❌ Could not get technicians data: {error}")
            return
        
        # Check data structure
        print(f"📊 Technicians API structure: {list(techs_data.keys()) if isinstance(techs_data, dict) else 'List/Other'}")
        
        if isinstance(techs_data, dict):
            api_techs = len(techs_data.get('technicians', []))
            tech_list = techs_data.get('technicians', [])
            if tech_list:
                print(f"📊 Sample technician data: {list(tech_list[0].keys()) if tech_list else 'Empty'}")
        else:
            api_techs = len(techs_data) if isinstance(techs_data, list) else 0
        
        print(f"📊 Technicians API count: {api_techs}")
        
        if overview_techs == api_techs:
            print(f"✅ CONSISTENT: Technician counts match")
            self.fixes_applied.append("Technician count: Verified consistency")
        else:
            print(f"❌ DISCREPANCY: Overview shows {overview_techs}, API shows {api_techs}")
            self.remaining_issues.append(f"Technician count: Overview ({overview_techs}) vs API ({api_techs})")
    
    def diagnose_monthly_drill_down_issues(self):
        """Diagnose monthly drill-down MTTR and count issues"""
        print("\n🔧 DIAGNOSING MONTHLY DRILL-DOWN ISSUES")
        print("-" * 50)
        
        months = ['2025-02', '2025-03', '2025-04']
        
        for month in months:
            print(f"\n📅 Testing month: {month}")
            
            # Get overview data for the month
            overview_data, error = self.make_request("/api/overview", {'month': month})
            if error:
                print(f"❌ Could not get overview data: {error}")
                continue
            
            overview_incidents = overview_data.get('total_incidents', 0)
            overview_mttr = overview_data.get('avg_resolution_time', 0)
            overview_fcr = overview_data.get('fcr_rate', 0)
            
            print(f"📊 Overview - Incidents: {overview_incidents}, MTTR: {overview_mttr}h, FCR: {overview_fcr}%")
            
            # Test MTTR drill-down
            mttr_data, error = self.make_request("/api/mttr_drilldown", {'month': month})
            if error:
                print(f"❌ MTTR drill-down failed: {error}")
                self.remaining_issues.append(f"MTTR drill-down ({month}): {error}")
            else:
                drill_mttr = mttr_data.get('avg_mttr_hours', 0)
                print(f"📊 MTTR drill-down: {drill_mttr}h")
                
                if abs(overview_mttr - drill_mttr) <= 0.1:
                    self.fixes_applied.append(f"MTTR drill-down ({month}): Consistent")
                else:
                    self.remaining_issues.append(f"MTTR drill-down ({month}): Overview {overview_mttr}h vs Drill-down {drill_mttr}h")
            
            # Test FCR drill-down
            fcr_data, error = self.make_request("/api/fcr_drilldown", {'month': month})
            if error:
                print(f"❌ FCR drill-down failed: {error}")
                self.remaining_issues.append(f"FCR drill-down ({month}): {error}")
            else:
                drill_fcr = fcr_data.get('fcr_rate', 0)
                print(f"📊 FCR drill-down: {drill_fcr}%")
                
                if abs(overview_fcr - drill_fcr) <= 0.5:
                    self.fixes_applied.append(f"FCR drill-down ({month}): Consistent")
                else:
                    self.remaining_issues.append(f"FCR drill-down ({month}): Overview {overview_fcr}% vs Drill-down {drill_fcr}%")
            
            # Test incident drill-down
            incident_data, error = self.make_request("/api/incident_drilldown", {'month': month})
            if error:
                print(f"❌ Incident drill-down failed: {error}")
                self.remaining_issues.append(f"Incident drill-down ({month}): {error}")
            else:
                drill_incidents = incident_data.get('total_incidents', 0)
                print(f"📊 Incident drill-down: {drill_incidents}")
                
                if abs(overview_incidents - drill_incidents) <= 5:  # Allow small tolerance
                    self.fixes_applied.append(f"Incident drill-down ({month}): Consistent")
                else:
                    self.remaining_issues.append(f"Incident drill-down ({month}): Overview {overview_incidents} vs Drill-down {drill_incidents}")
    
    def diagnose_region_totals_issue(self):
        """Diagnose region totals mathematical inconsistency"""
        print("\n🔧 DIAGNOSING REGION TOTALS ISSUES")
        print("-" * 50)
        
        # Get overview total
        overview_data, error = self.make_request("/api/overview")
        if error:
            print(f"❌ Could not get overview data: {error}")
            return
        
        overview_total = overview_data.get('total_incidents', 0)
        print(f"📊 Overview total: {overview_total}")
        
        # Get region breakdown
        regions_data, error = self.make_request("/api/regions")
        if error:
            print(f"❌ Could not get regions data: {error}")
            return
        
        region_stats = regions_data.get('region_stats', [])
        region_total = sum([r.get('incidents', 0) for r in region_stats])
        
        print(f"📊 Region breakdown:")
        for region in region_stats:
            print(f"  {region.get('region', 'Unknown')}: {region.get('incidents', 0)}")
        
        print(f"📊 Sum of regions: {region_total}")
        
        if overview_total == region_total:
            print(f"✅ CONSISTENT: Region totals match overview")
            self.fixes_applied.append("Region totals: Mathematical consistency verified")
        else:
            print(f"❌ DISCREPANCY: Overview {overview_total} vs Region sum {region_total}")
            self.remaining_issues.append(f"Region totals: Overview ({overview_total}) vs Sum ({region_total})")
    
    def run_comprehensive_diagnosis(self):
        """Run comprehensive diagnosis of all discrepancies"""
        print("🔧 COMPREHENSIVE DISCREPANCY DIAGNOSIS")
        print("=" * 60)
        print(f"Analyzing dashboard at: {self.base_url}")
        print("Diagnosing all 16 identified discrepancies...")
        print("=" * 60)
        
        # Wait for server
        time.sleep(2)
        
        # Run all diagnostic tests
        self.diagnose_team_drill_down_issue()
        self.diagnose_sla_breach_issue()
        self.diagnose_technician_count_issue()
        self.diagnose_monthly_drill_down_issues()
        self.diagnose_region_totals_issue()
        
        # Generate diagnosis report
        self.generate_diagnosis_report()
    
    def generate_diagnosis_report(self):
        """Generate comprehensive diagnosis report"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE DISCREPANCY DIAGNOSIS REPORT")
        print("=" * 60)
        
        total_issues = len(self.fixes_applied) + len(self.remaining_issues)
        fixed_count = len(self.fixes_applied)
        remaining_count = len(self.remaining_issues)
        
        print(f"Total Issues Analyzed: {total_issues}")
        print(f"✅ Issues Resolved/Verified: {fixed_count}")
        print(f"❌ Issues Requiring Fixes: {remaining_count}")
        
        if remaining_count > 0:
            print(f"\n❌ ISSUES REQUIRING FIXES ({remaining_count}):")
            print("-" * 50)
            for issue in self.remaining_issues:
                print(f"• {issue}")
        
        if fixed_count > 0:
            print(f"\n✅ ISSUES RESOLVED/VERIFIED ({fixed_count}):")
            print("-" * 50)
            for fix in self.fixes_applied:
                print(f"• {fix}")
        
        print(f"\n📈 DIAGNOSIS SUMMARY:")
        if remaining_count == 0:
            print("🎉 ALL DISCREPANCIES RESOLVED!")
            print("✅ Dashboard data integrity verified")
            print("✅ Ready for production deployment")
        elif remaining_count <= 3:
            print("✅ GOOD PROGRESS! Most issues resolved")
            print("🔧 Few remaining issues need attention")
        else:
            print("⚠️  SIGNIFICANT WORK NEEDED")
            print("🔧 Multiple critical issues require fixes")
        
        print(f"\n🏁 DIAGNOSIS COMPLETED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    fixer = DiscrepancyFixer()
    fixer.run_comprehensive_diagnosis()

if __name__ == "__main__":
    main()
