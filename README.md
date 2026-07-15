# VulnShield

A vulnerability scanner with an interactive reporting dashboard.

## Overview

VulnShield integrates NMAP and ZAP scanning tools to identify vulnerabilities in web applications and network systems. The application scores risks using CVSS and EPSS metrics and displays interactive reports through a user-friendly dashboard.

## Features

- Vulnerability scanning using NMAP (NSE) and ZAP (Active & Passive)
- Automated risk assessment and scoring
- Interactive vulnerability reports with visual representations
- Beginner-friendly interface

## Tech Stack

- **Frontend**: HTML, Tailwind CSS, JavaScript, Chart.js
- **Backend**: Python, Flask
- **Scanning Tools**: NMAP, OWASP ZAP
- **Database**: PostgreSQL

## Requirements

- Python 3.7 or higher
- PostgreSQL database
- NMAP scanner
- OWASP ZAP (optional but recommended)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/vulnshield.git
   cd vulnshield
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install external tools:
   - **NMAP**: Download and install from [https://nmap.org/download.html](https://nmap.org/download.html)
   - **ZAP**: Download and install from [https://www.zaproxy.org/download/](https://www.zaproxy.org/download/)

4. Configure PostgreSQL:
   - Create a database named `vulnshield`
   - Update the database connection parameters in `backend/database/db_handler.py` if needed

## Running the Application

You can run the application using the provided run script:

```
python run.py
```

This script will:
- Check if all dependencies are installed
- Initialize the database if needed
- Start the VulnShield web application

Alternatively, you can run it directly:

```
python backend/app.py
```

Once running, access the web interface at `http://localhost:5000`

## Usage Guide

1. **Start a Scan**:
   - Go to the Scanner section
   - Enter a target URL or IP address
   - Select scan type (Full, NMAP only, or ZAP only)
   - Click "Start Scan"

2. **View Reports**:
   - Go to the Reports section
   - Click on any report to view details
   - Explore interactive charts and vulnerability findings

3. **Analyze Vulnerabilities**:
   - Review risk scores and severity levels
   - Check recommended actions for each vulnerability
   - Search and filter vulnerabilities as needed

## Development

To contribute to VulnShield:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
