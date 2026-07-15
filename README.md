# VulnShield 🛡️

A modern, enterprise-grade vulnerability scanner with an interactive Security Operations Center (SOC) reporting dashboard.

**🔴 Live Demo:** [https://vulnshield-b0v2.onrender.com](https://vulnshield-b0v2.onrender.com)

## Overview

VulnShield integrates **NMAP** and **ZAP (Zed Attack Proxy)** scanning tools to identify vulnerabilities in web applications and network systems. The application scores risks using CVSS and EPSS metrics and displays interactive reports through a beautifully designed, responsive SOC dashboard featuring a premium dark theme.

## ✨ Features

- **Automated Scanning**: Comprehensive vulnerability scanning using NMAP (NSE) and ZAP (Active & Passive).
- **Risk Assessment**: Automated risk scoring leveraging industry-standard CVSS and EPSS metrics.
- **SOC Dashboard**: A modern, dark-mode (`#0F172A`) user interface with real-time progress indicators and sleek micro-animations.
- **Interactive Reports**: Visual data representations using Chart.js to help analysts pinpoint critical vulnerabilities instantly.
- **Cloud Ready**: Containerized via Docker and fully optimized for cloud deployments like Render.

## 🛠 Tech Stack

- **Frontend**: HTML5, Vanilla CSS (Custom Design System), JavaScript, Chart.js
- **Backend**: Python 3.10+, Flask
- **Scanning Tools**: NMAP, OWASP ZAP (zap-cli)
- **Database**: PostgreSQL (with psycopg2-binary)
- **Deployment**: Docker, Render

## 🚀 Installation & Local Development

### Prerequisites

- Python 3.10+
- PostgreSQL database
- NMAP scanner
- OWASP ZAP CLI (`zap-cli`)

### Setup Instructions

1. **Clone this repository:**
   ```bash
   git clone https://github.com/sahil-khohari/vulnshield.git
   cd vulnshield
   ```

2. **Create and activate a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install required dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install external security tools:**
   - **NMAP**: Download and install from [nmap.org](https://nmap.org/download.html)
   - **ZAP**: Make sure the `zap-cli` binary is in your system PATH.

5. **Configure PostgreSQL:**
   - Create a database named `vulnshield`
   - Ensure your PostgreSQL service is running on the default port. Update connection parameters in `backend/database/db_handler.py` if necessary.

6. **Run the Application:**
   ```bash
   python run.py
   ```
   *The application runs on `http://localhost:5005` by default.*

## 🐳 Docker Deployment

VulnShield is fully containerized. To build and run it via Docker:

```bash
docker build -t vulnshield .
docker run -p 5000:5000 vulnshield
```

## 📖 Usage Guide

1. **Start a Scan**:
   - Navigate to the **Scanner** section from the sidebar.
   - Enter a target URL or IP address.
   - Select your desired scan type (Full, NMAP only, or ZAP only).
   - Click "Start Scan" and monitor the real-time console output.
2. **View Reports**:
   - Navigate to the **Reports** section to see all completed scans.
   - Click on any report to view deep-dive analytics.
3. **Analyze Vulnerabilities**:
   - Review the dashboard's interactive charts.
   - Filter findings by severity (Critical, High, Medium, Low) to prioritize remediation.

## 👨‍💻 Developer

**Sahil Khohari**
- Background: Student at VIT Bhopal University.
- Core Focus: Cybersecurity and software vulnerability testing.
- Technical Skills: Competitive programming (C++), network scanning tools (Nmap, Nessus), and Kali Linux environments.

---
*© 2026 VulnShield. All rights reserved.*
