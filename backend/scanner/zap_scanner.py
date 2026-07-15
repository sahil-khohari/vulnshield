import subprocess
import tempfile
import os
import xmltodict
import json
import re
import datetime

class ZapScanner:
    def __init__(self, zap_path=None, api_key=None):
        """
        Initialize ZAP scanner
        
        Args:
            zap_path (str): Path to ZAP executable (optional)
            api_key (str): ZAP API key (optional)
        """
        # Base ZAP directory - use the full path from environment variable
        self.zap_base_dir = zap_path if zap_path else 'C:\\Program Files\\ZAP\\Zed Attack Proxy'
        
        # Normalize path to handle Windows path separators
        self.zap_base_dir = os.path.normpath(self.zap_base_dir)
        self.zap_jar = os.path.join(self.zap_base_dir, 'zap-2.16.1.jar')
        
        print(f"Looking for ZAP JAR at: {self.zap_jar}")
        
        # Verify the JAR file exists
        if not os.path.exists(self.zap_jar):
            print(f"[WARNING] ZAP JAR file not found at: {self.zap_jar}")
            print("ZAP scanning will not be available.")
            self.zap_jar = None
        else:
            print(f"Found ZAP JAR at: {self.zap_jar}")
        
        print(f"Found ZAP JAR at: {self.zap_jar}")
        print(f"Using ZAP base directory: {self.zap_base_dir}")
        
        self.api_key = api_key or ''
    
    def run_scan(self, target, scan_type='active'):
        """
        Run a ZAP scan against the target with no timeout
        
        Args:
            target (str): Target URL to scan
            scan_type (str): Type of scan to run (active, passive, or full)
            
        Returns:
            dict: Scan results including vulnerabilities
        """
        result = {
            'target': target,
            'scan_type': scan_type,
            'vulnerabilities': []
        }
        
        try:
            # Ensure target has protocol
            if not target.startswith(('http://', 'https://')):
                target = 'http://' + target
            
            # Create a user-writable home directory for ZAP
            user_home = os.path.expanduser('~')
            zap_home = os.path.join(user_home, '.ZAP')
            os.makedirs(zap_home, exist_ok=True)
            
            # Create temp directory for ZAP output
            with tempfile.TemporaryDirectory() as temp_dir:
                output_file = os.path.join(temp_dir, 'zap_results.xml')
                
                # Create a custom environment with ZAP_HOME set
                custom_env = os.environ.copy()
                custom_env['ZAP_HOME'] = zap_home
                
                # Define ZAP command with optimized settings for more reliable scanning
                cmd = [
                    'java',
                    '-Xmx1024m',                         # Increased memory for better performance
                    '-jar', self.zap_jar,                # JAR file path
                    '-cmd',                              # Command line mode
                    '-quickurl', target,                 # URL to scan
                    '-quickout', output_file,            # Output file
                    '-quickprogress',                    # Show progress
                    '-silent',                           # Reduce console output
                    # Optimized scan configuration for better completion rates
                    '-config', 'scanner.attackOnStart=true',
                    '-config', 'scanner.threadPerHost=3',  # Increased threads for faster scanning
                    '-config', 'spider.maxDuration=0',     # No spider timeout
                    '-config', 'ajaxSpider.maxDuration=0', # No AJAX spider timeout
                    '-config', 'scanner.maxDuration=0',    # No scanner timeout
                    '-config', 'scanner.maxRuleDurationInMins=0', # No rule timeout
                    # Focus on important vulnerabilities to reduce scan time
                    '-config', 'scanner.attackStrength=MEDIUM', # Medium attack strength for balance
                    '-config', 'scanner.alertThreshold=MEDIUM', # Medium alert threshold
                    # Limit crawling depth to improve completion rates
                    '-config', 'spider.maxDepth=5',
                    # Disable unnecessary features
                    '-config', 'ajaxSpider.clickDefaultElems=false',
                    '-config', 'ajaxSpider.clickElemsOnce=true',
                ]
                
                print(f"Running ZAP scan with command: {' '.join(cmd)}")
                print("ZAP scan will run until completion - no timeout set")
                
                # Start ZAP process
                start_time = datetime.datetime.now()
                process = subprocess.Popen(
                    cmd,
                    env=custom_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Wait for ZAP to complete
                stdout, stderr = process.communicate()
                
                end_time = datetime.datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                print(f"ZAP scan completed in {duration:.2f} seconds")
                
                # Generate basic results even if the output file wasn't created
                if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                    print("No ZAP output file generated, creating minimal results")
                    result['vulnerabilities'] = self._generate_minimal_results(target)
                    result['duration'] = duration
                    result['note'] = "Scan completed but no results were generated. This may indicate the target was not accessible."
                    return result
                
                # Parse the XML output for vulnerabilities
                with open(output_file, 'r') as f:
                    xml_content = f.read()
                
                if not xml_content.strip():
                    print("Empty ZAP output file, creating minimal results")
                    result['vulnerabilities'] = self._generate_minimal_results(target)
                else:
                    result_dict = xmltodict.parse(xml_content)
                    result = self._process_cli_results(result_dict, target)
                
                result['duration'] = duration
                return result
        
        except Exception as e:
            print(f"Error running ZAP scan: {str(e)}")
            if hasattr(e, 'stderr') and e.stderr:
                print(f"Error details: {e.stderr}")
            
            # Return basic results even on error
            result['error'] = str(e)
            result['vulnerabilities'] = self._generate_minimal_results(target)
            return result
            
    def _generate_minimal_results(self, target):
        """Generate minimal vulnerability results when scan fails or times out"""
        return [{
            'name': 'Scan Incomplete',
            'description': 'The ZAP scan was terminated before completion. This could be due to timeout, connection issues, or the target website being too large to scan completely in the allocated time.',
            'severity': 3.5,
            'risk_level': 'low',
            'confidence': 'medium',
            'url': target,
            'cvss_score': 3.5,
            'epss_score': 0.01,
            'risk_score': 2.85,
            'solution': 'Try the following options:\n1. Run a more targeted scan on specific paths instead of the entire website\n2. Increase the scan timeout duration\n3. Check if the target website is accessible and responding properly\n4. If the website is very large, consider breaking the scan into smaller segments',
            'reference': 'https://www.zaproxy.org/docs/desktop/start/features/scan/',
            'cwe_id': '',
            'scan_status': 'incomplete',
            'recommendations': [
                'Focus on scanning specific critical paths rather than the entire website',
                'Increase the scan timeout in the settings',
                'Verify the target is accessible before scanning',
                'For large websites, scan individual sections separately'
            ]
        }]
    
    def _process_cli_results(self, result_dict, target):
        """Process ZAP CLI results from XML"""
        result = {
            'target': target,
            'scan_type': 'cli',
            'vulnerabilities': []
        }
        
        # Extract site information
        try:
            sites = result_dict.get('OWASPZAPReport', {}).get('site', [])
            if not isinstance(sites, list):
                sites = [sites]
            
            for site in sites:
                # Handle case where no alerts were found
                if not site.get('alerts'):
                    continue
                    
                alerts = site.get('alerts', {}).get('alertitem', [])
                
                if not isinstance(alerts, list):
                    alerts = [alerts]
                
                for alert in alerts:
                    # Extract alert information
                    name = alert.get('name', 'Unknown')
                    risk = alert.get('riskdesc', 'Unknown')
                    description = alert.get('desc', '')
                    solution = alert.get('solution', '')
                    reference = alert.get('reference', '')
                    
                    # Extract instances
                    instances = alert.get('instances', {}).get('instance', [])
                    if not isinstance(instances, list):
                        instances = [instances]
                    
                    for instance in instances:
                        url = instance.get('uri', target)
                        
                        # Map risk level to severity score
                        risk_level = risk.split(' ')[0].lower() if risk else 'info'
                        severity_map = {
                            'high': 7.5,
                            'medium': 5.0,
                            'low': 2.5,
                            'info': 1.0
                        }
                        severity = severity_map.get(risk_level, 1.0)
                        
                        # Calculate risk score with improved formula
                        cvss_score = severity
                        
                        # Assign EPSS score based on risk level
                        epss_map = {
                            'high': 0.1,
                            'medium': 0.05,
                            'low': 0.02,
                            'info': 0.01
                        }
                        epss_score = epss_map.get(risk_level, 0.01)
                        
                        # Calculate risk score - ensure it's never zero
                        risk_score = max((cvss_score * 0.7) + (epss_score * 100 * 0.3), 1.0)
                        
                        # Create vulnerability entry
                        vuln = {
                            'name': name,
                            'description': description,
                            'severity': severity,
                            'risk_level': risk_level,
                            'confidence': alert.get('confidence', '').lower(),
                            'url': url,
                            'cvss_score': cvss_score,
                            'epss_score': epss_score,
                            'risk_score': risk_score,
                            'solution': solution,
                            'reference': reference,
                            'cwe_id': alert.get('cweid', ''),
                            'source': 'zap'
                        }
                        
                        result['vulnerabilities'].append(vuln)
            
            return result
        except Exception as e:
            print(f"Error processing ZAP results: {str(e)}")
            return result