import nmap
import xml.etree.ElementTree as ET
import xmltodict
import json
import subprocess
import tempfile
import os
import re

class NmapScanner:
    def __init__(self):
        self.scanner = nmap.PortScanner()
    
    def run_scan(self, target, scan_type='vuln'):
        """
        Run an Nmap vulnerability scan against the target
        
        Args:
            target (str): Target hostname or IP address
            scan_type (str): Type of scan to run (vuln, basic, etc.)
            
        Returns:
            dict: Scan results including vulnerabilities
        """
        result = {
            'target': target,
            'scan_type': scan_type,
            'vulnerabilities': []
        }
        
        try:
            if scan_type == 'vuln':
                # Use Nmap's vulnerability scripts (NSE) for scanning
                self._run_vulnerability_scan(target, result)
            else:
                # Run a basic scan
                self._run_basic_scan(target, result)
                
            return result
        except Exception as e:
            print(f"Error running Nmap scan: {str(e)}")
            result['error'] = str(e)
            return result
    
    def _run_basic_scan(self, target, result):
        """Run a basic Nmap scan"""
        self.scanner.scan(target, arguments='-sV -sS -T4 -O')
        
        result['hosts'] = []
        
        for host in self.scanner.all_hosts():
            host_info = {
                'host': host,
                'state': self.scanner[host].state(),
                'open_ports': []
            }
            
            for protocol in self.scanner[host].all_protocols():
                for port in self.scanner[host][protocol].keys():
                    port_info = self.scanner[host][protocol][port]
                    host_info['open_ports'].append({
                        'port': port,
                        'protocol': protocol,
                        'service': port_info.get('name', ''),
                        'product': port_info.get('product', ''),
                        'version': port_info.get('version', '')
                    })
            
            result['hosts'].append(host_info)
    
    def _run_vulnerability_scan(self, target, result):
        """Run a vulnerability scan using Nmap NSE scripts"""
        # Create a temporary file to store XML output
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as temp_file:
            xml_output = temp_file.name
        
        try:
            # Run nmap with vulnerability scripts and XML output
            cmd = [
                'nmap', 
                '-sV',                          # Version detection
                '--script', 'vuln',             # Use vulnerability scripts
                '-T4',                          # Aggressive timing
                '-oX', xml_output,              # Output to XML
                target
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # Parse the XML output
            tree = ET.parse(xml_output)
            root = tree.getroot()
            
            # Convert XML to dict
            scan_dict = xmltodict.parse(ET.tostring(root))
            
            # Extract hosts and vulnerabilities
            if 'nmaprun' in scan_dict and 'host' in scan_dict['nmaprun']:
                hosts = scan_dict['nmaprun']['host']
                if not isinstance(hosts, list):
                    hosts = [hosts]
                
                result['hosts'] = []
                
                for host in hosts:
                    host_info = self._extract_host_info(host)
                    result['hosts'].append(host_info)
                    
                    # Extract vulnerabilities from scripts
                    vulns = self._extract_vulnerabilities(host)
                    result['vulnerabilities'].extend(vulns)
            
            # Add basic vulnerability findings if none found
            if not result['vulnerabilities']:
                # Check for open ports with known vulnerabilities
                for host_info in result.get('hosts', []):
                    for port in host_info.get('open_ports', []):
                        service = port.get('service', '').lower()
                        product = port.get('product', '').lower()
                        version = port.get('version', '')
                        
                        # Add simple vulnerability detection based on service/version
                        if any(s in service for s in ['http', 'www', 'web']):
                            if 'apache' in product and version.startswith('2.4.'):
                                # Example of a basic vulnerability finding
                                result['vulnerabilities'].append({
                                    'name': 'Potential Apache Vulnerability',
                                    'description': f'Apache {version} may have known vulnerabilities',
                                    'severity': 5.0,
                                    'port': port.get('port'),
                                    'cvss_score': 5.0,
                                    'epss_score': 0.01,
                                    'risk_score': 4.5
                                })
        
        finally:
            # Clean up temp file
            if os.path.exists(xml_output):
                os.remove(xml_output)
    
    def _extract_host_info(self, host_dict):
        """Extract host information from Nmap XML dict"""
        host_info = {
            'host': host_dict.get('address', {}).get('@addr', ''),
            'state': host_dict.get('status', {}).get('@state', ''),
            'open_ports': []
        }
        
        # Extract ports
        if 'ports' in host_dict and 'port' in host_dict['ports']:
            ports = host_dict['ports']['port']
            
            if not isinstance(ports, list):
                ports = [ports]
            
            for port in ports:
                if port.get('state', {}).get('@state') == 'open':
                    port_info = {
                        'port': int(port.get('@portid', 0)),
                        'protocol': port.get('@protocol', ''),
                        'service': port.get('service', {}).get('@name', ''),
                        'product': port.get('service', {}).get('@product', ''),
                        'version': port.get('service', {}).get('@version', '')
                    }
                    host_info['open_ports'].append(port_info)
        
        return host_info
    
    def _extract_vulnerabilities(self, host_dict):
        """Extract vulnerabilities from Nmap script output"""
        vulnerabilities = []
        
        # Extract from scripts at host level
        if 'hostscript' in host_dict and 'script' in host_dict['hostscript']:
            scripts = host_dict['hostscript']['script']
            if not isinstance(scripts, list):
                scripts = [scripts]
            
            for script in scripts:
                vulns = self._parse_script_output(script)
                vulnerabilities.extend(vulns)
        
        # Extract from scripts at port level
        if 'ports' in host_dict and 'port' in host_dict['ports']:
            ports = host_dict['ports']['port']
            
            if not isinstance(ports, list):
                ports = [ports]
            
            for port in ports:
                if 'script' in port:
                    scripts = port['script']
                    
                    if not isinstance(scripts, list):
                        scripts = [scripts]
                        
                    port_num = int(port.get('@portid', 0))
                    
                    for script in scripts:
                        vulns = self._parse_script_output(script, port_num)
                        vulnerabilities.extend(vulns)
        
        return vulnerabilities
    
    def _parse_script_output(self, script, port=None):
        """Parse vulnerability information from a script output"""
        vulns = []
        
        # Check if it's a vulnerability script
        script_id = script.get('@id', '')
        output = script.get('@output', '')
        
        # Common vulnerability scripts in Nmap NSE
        vuln_scripts = [
            'vulners', 'vuln', 'vulscan', 'ssl-heartbleed', 'ssl-poodle', 
            'smb-vuln', 'http-vuln', 'ftp-vuln'
        ]
        
        if any(vs in script_id for vs in vuln_scripts):
            # Try to extract CVE IDs and other vuln info
            cve_pattern = r'CVE-\d{4}-\d{4,7}'
            cves = re.findall(cve_pattern, output)
            
            # Extract CVSS if available
            cvss_pattern = r'CVSS\s*:?\s*(\d+\.\d+)'
            cvss_match = re.search(cvss_pattern, output)
            cvss_score = float(cvss_match.group(1)) if cvss_match else 5.0  # Default score
            
            # Simple severity mapping based on CVSS
            severity_mapping = {
                (0, 4): 'Low',
                (4, 7): 'Medium',
                (7, 9): 'High',
                (9, 10): 'Critical'
            }
            
            severity_text = next((sev for (low, high), sev in severity_mapping.items() 
                                  if low <= cvss_score < high), 'Medium')
            
            # Create vulnerability entry
            vuln = {
                'name': script_id,
                'description': output,  # Store the full output without truncation
                'severity': cvss_score,
                'cves': cves,
                'cvss_score': cvss_score,
                'severity_text': severity_text,
                'epss_score': 0.01,  # Would need API call to get real EPSS
                'script_output': output,
                'risk_score': min(cvss_score * 0.8 + 2, 10)  # Simple risk calculation
            }
            
            if port:
                vuln['port'] = port
                
            vulns.append(vuln)
        
        return vulns
