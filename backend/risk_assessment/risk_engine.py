import json
import math
import re
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RiskEngine:
    def __init__(self):
        """Initialize the risk assessment engine"""
        # Get weights from environment variables or use defaults
        self.weight_cvss = float(os.getenv("WEIGHT_CVSS", 0.7))
        self.weight_epss = float(os.getenv("WEIGHT_EPSS", 0.3))
        
        # Mock threat intelligence data (would be replaced with real API calls)
        self.threat_intelligence = self._load_mock_threat_intel()
    
    def calculate_risk(self, scan_results):
        """
        Calculate risk scores for vulnerabilities in scan results
        
        Args:
            scan_results (dict): Results from vulnerability scanners
            
        Returns:
            dict: Risk scores and assessment
        """
        risk_scores = {
            'overall_score': 0,
            'vulnerabilities': [],
            'summary': {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            }
        }
        
        # Collect all vulnerabilities
        all_vulns = []
        
        # Process Nmap vulnerabilities
        if 'nmap' in scan_results and 'vulnerabilities' in scan_results['nmap']:
            for vuln in scan_results['nmap']['vulnerabilities']:
                vuln['source'] = 'nmap'
                all_vulns.append(vuln)
        
        # Process ZAP vulnerabilities
        if 'zap' in scan_results and 'vulnerabilities' in scan_results['zap']:
            for vuln in scan_results['zap']['vulnerabilities']:
                vuln['source'] = 'zap'
                all_vulns.append(vuln)
        
        # Calculate risk score for each vulnerability
        for vuln in all_vulns:
            risk_score = self._calculate_vulnerability_risk(vuln)
            vuln['risk_score'] = risk_score
            
            # Categorize by severity
            if risk_score >= 9:
                severity = 'critical'
            elif risk_score >= 7:
                severity = 'high'
            elif risk_score >= 4:
                severity = 'medium'
            else:
                severity = 'low'
            
            vuln['severity_category'] = severity
            risk_scores['summary'][severity] += 1
            
            # Add to vulnerabilities list with assessment
            risk_scores['vulnerabilities'].append({
                'name': vuln.get('name', 'Unknown'),
                'source': vuln.get('source', ''),
                'cvss_score': vuln.get('cvss_score', 0),
                'epss_score': vuln.get('epss_score', 0),
                'risk_score': risk_score,
                'severity': severity,
                'description': vuln.get('description', ''),
                'recommendation': self._generate_recommendation(vuln, risk_score)
            })
        
        # Calculate overall risk score (weighted average of top 5 vulnerabilities)
        if risk_scores['vulnerabilities']:
            # Sort by risk score (descending)
            sorted_vulns = sorted(
                risk_scores['vulnerabilities'],
                key=lambda x: x['risk_score'],
                reverse=True
            )
            
            # Take top 5 or all if less than 5
            top_vulns = sorted_vulns[:min(5, len(sorted_vulns))]
            
            # Calculate weighted average
            overall_score = sum(v['risk_score'] for v in top_vulns) / len(top_vulns)
            risk_scores['overall_score'] = round(overall_score, 2)
        
        return risk_scores
    
    def _calculate_vulnerability_risk(self, vuln):
        """
        Calculate risk score for a single vulnerability
        
        Formula: Risk Score = (CVSS Score * Weight_CVSS) + (EPSS Score * Weight_EPSS * 10) + Threat Adjustment
        """
        # Get CVSS score (default to 5.0 if not present)
        cvss_score = vuln.get('cvss_score', 5.0)
        
        # Get EPSS score (default to 0.01 if not present)
        epss_score = vuln.get('epss_score', 0.01)
        
        # Get CVEs for threat intelligence lookup
        cves = vuln.get('cves', [])
        if isinstance(cves, str):
            # Extract CVEs from string if needed
            cve_pattern = r'CVE-\d{4}-\d{4,7}'
            cves = re.findall(cve_pattern, cves)
        
        # Calculate threat adjustment based on threat intelligence
        threat_adjustment = 0
        
        if cves:
            for cve in cves:
                threat_info = self._get_threat_intel(cve)
                if threat_info:
                    # Adjust based on threat intelligence
                    if threat_info.get('active_exploitation', False):
                        threat_adjustment += 1.5
                    
                    if threat_info.get('in_the_wild', False):
                        threat_adjustment += 1.0
                    
                    # Adjust based on age (newer = higher risk)
                    age_factor = self._calculate_age_factor(threat_info.get('published_date'))
                    threat_adjustment += age_factor
        
        # Calculate preliminary risk score
        preliminary_score = (cvss_score * self.weight_cvss) + (epss_score * self.weight_epss * 10) + threat_adjustment
        
        # Cap at 10
        final_score = min(preliminary_score, 10)
        
        return round(final_score, 2)
    
    def _calculate_age_factor(self, published_date):
        """Calculate risk adjustment factor based on vulnerability age"""
        if not published_date:
            return 0
        
        try:
            # Parse date
            pub_date = datetime.strptime(published_date, "%Y-%m-%d")
            current_date = datetime.now()
            
            # Calculate age in days
            age_days = (current_date - pub_date).days
            
            # Newer vulnerabilities get higher adjustment (max 1.0 for brand new, decreases over time)
            if age_days <= 30:  # Less than a month old
                return 1.0
            elif age_days <= 90:  # 1-3 months old
                return 0.7
            elif age_days <= 180:  # 3-6 months old
                return 0.4
            elif age_days <= 365:  # 6-12 months old
                return 0.2
            else:  # Over a year old
                return 0
                
        except:
            return 0
    
    def _get_threat_intel(self, cve_id):
        """Get threat intelligence for a CVE"""
        # In a real implementation, this would call an external API
        # For now, we use mock data
        return self.threat_intelligence.get(cve_id)
    
    def _load_mock_threat_intel(self):
        """Load mock threat intelligence data"""
        # This would be replaced with real threat intel feeds
        return {
            "CVE-2021-44228": {  # Log4Shell
                "active_exploitation": True,
                "in_the_wild": True,
                "published_date": "2021-12-10",
                "threat_level": "Critical"
            },
            "CVE-2021-40539": {  # ADSelfService Plus
                "active_exploitation": True,
                "in_the_wild": True,
                "published_date": "2021-09-07",
                "threat_level": "High"
            },
            "CVE-2021-26855": {  # ProxyLogon
                "active_exploitation": True,
                "in_the_wild": True,
                "published_date": "2021-03-02",
                "threat_level": "Critical"
            },
            "CVE-2022-22965": {  # Spring4Shell
                "active_exploitation": True,
                "in_the_wild": True,
                "published_date": "2022-03-31",
                "threat_level": "Critical"
            },
            "CVE-2022-30190": {  # Follina
                "active_exploitation": True,
                "in_the_wild": True,
                "published_date": "2022-05-30",
                "threat_level": "High"
            }
        }
    
    def _generate_recommendation(self, vuln, risk_score):
        """Generate recommendations based on vulnerability and risk score"""
        recommendations = []
        
        # Basic recommendation based on severity
        if risk_score >= 9:
            recommendations.append("Immediate remediation required. Apply patches or mitigations as soon as possible.")
        elif risk_score >= 7:
            recommendations.append("High priority for remediation. Schedule patching within the next 7 days.")
        elif risk_score >= 4:
            recommendations.append("Medium priority. Address within standard patch cycles.")
        else:
            recommendations.append("Low priority. Address during routine maintenance.")
        
        # Specific recommendations based on vulnerability type
        vuln_name = vuln.get('name', '').lower()
        vuln_desc = vuln.get('description', '').lower()
        
        # SQL injection recommendations
        if any(term in vuln_name or term in vuln_desc for term in ['sql', 'injection', 'sqli']):
            recommendations.append("Implement parameterized queries or prepared statements to prevent SQL injection.")
            recommendations.append("Apply input validation and sanitization for all user inputs.")
            
        # XSS recommendations
        if any(term in vuln_name or term in vuln_desc for term in ['xss', 'cross-site', 'script']):
            recommendations.append("Apply proper output encoding based on the context of output.")
            recommendations.append("Implement Content Security Policy (CSP) headers.")
            
        # Authentication issues
        if any(term in vuln_name or term in vuln_desc for term in ['auth', 'password', 'credential']):
            recommendations.append("Review authentication mechanisms and implement multi-factor authentication where possible.")
            recommendations.append("Enforce strong password policies and account lockout procedures.")
            
        # SSL/TLS issues
        if any(term in vuln_name or term in vuln_desc for term in ['ssl', 'tls', 'cert', 'cipher']):
            recommendations.append("Update SSL/TLS configuration to use only secure protocols and ciphers.")
            recommendations.append("Implement proper certificate validation and management.")
        
        # If solution is provided by the scanner, add it
        if 'solution' in vuln and vuln['solution']:
            recommendations.append(f"Scanner recommendation: {vuln['solution']}")
        
        return recommendations
