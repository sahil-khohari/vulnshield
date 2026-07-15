#!/usr/bin/env python3
"""
VulnShield Launcher Script
This script checks dependencies and starts the VulnShield application.
"""

import os
import sys
import subprocess
import shutil

def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []
    
    # Check Python dependencies
    try:
        import flask
        import psycopg2
        import xmltodict
    except ImportError as e:
        missing_deps.append(str(e).split("'")[1])
    
    # Check external tools
    if not shutil.which('nmap'):
        missing_deps.append('nmap')
    
    if not shutil.which('zap-cli'):
        missing_deps.append('zap-cli')
    
    if 'zap-cli' in missing_deps:
        print("[WARNING] OWASP ZAP CLI not found in PATH. ZAP scanning functionality may be limited.")
    
    return missing_deps

def install_requirements():
    """Install Python requirements"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("[✓] Successfully installed Python dependencies")
        return True
    except subprocess.CalledProcessError:
        print("[✗] Failed to install Python dependencies")
        return False

def main():
    print("=" * 50)
    print("VulnShield - Vulnerability Scanner and Reporting Dashboard")
    print("=" * 50)
    
    # Check Python version
    python_version = sys.version.split()[0]
    print(f"[i] Python version: {python_version}")
    
    # Check if requirements.txt exists
    if os.path.exists('requirements.txt'):
        print("[i] Found requirements.txt")
    else:
        print("[✗] requirements.txt not found!")
        return 1
    
    # Check dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        print(f"[!] Missing dependencies: {', '.join(missing_deps)}")
        
        if all(dep not in ['nmap', 'zap-cli'] for dep in missing_deps):
            choice = input("Would you like to install the missing Python dependencies? (y/n): ").strip().lower()
            if choice == 'y':
                if install_requirements():
                    # Recheck dependencies after installation
                    missing_deps = check_dependencies()
                    if any(dep in ['nmap'] for dep in missing_deps):
                        print("[!] Please install the following tools manually:")
                        if 'nmap' in missing_deps:
                            print("  - NMAP: https://nmap.org/download.html")
                        if 'zap-cli' in missing_deps:
                            print("  - ZAP CLI: Install via package manager or from resources online.")
                        return 1
                else:
                    return 1
            else:
                print("[!] Dependencies must be installed to continue")
                return 1
        else:
            print("[!] Please install the following tools manually:")
            if 'nmap' in missing_deps:
                print("  - NMAP: https://nmap.org/download.html")
            if 'zap-cli' in missing_deps:
                print("  - ZAP CLI: Install via package manager or from resources online.")
            return 1
    
    print("[✓] All dependencies satisfied")
    
    # Start the application
    print("\n[i] Starting VulnShield...")
    try:
        from backend.app import app
        app.run(debug=False, host='0.0.0.0', port=int(os.getenv("PORT", 5005)))
    except Exception as e:
        print(f"[✗] Failed to start application: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
