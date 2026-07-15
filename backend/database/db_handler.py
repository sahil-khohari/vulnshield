import psycopg2
import json
import uuid
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseHandler:
    def __init__(self, host=None, port=None, database=None, user=None, password=None):
        self.conn_params = {
            "host": host or os.getenv("DB_HOST", "localhost"),
            "port": port or os.getenv("DB_PORT", "5432"),
            "database": database or os.getenv("DB_NAME", "vulnshield"),
            "user": user or os.getenv("DB_USER", "postgres"),
            "password": password or os.getenv("DB_PASSWORD", "postgres")
        }
    
    def get_connection(self):
        """Establish a connection to the PostgreSQL database"""
        try:
            print(f"Attempting to connect to database: {self.conn_params['database']} on {self.conn_params['host']}:{self.conn_params['port']} as {self.conn_params['user']}")
            return psycopg2.connect(**self.conn_params)
        except Exception as e:
            print(f"Database connection error: {str(e)}")
            print(f"Connection parameters: host={self.conn_params['host']}, port={self.conn_params['port']}, database={self.conn_params['database']}, user={self.conn_params['user']}")
            # During development/testing, create database if it doesn't exist
            self._create_database_if_not_exists()
            return psycopg2.connect(**self.conn_params)
    
    def _create_database_if_not_exists(self):
        """Create the database if it doesn't exist (for development)"""
        temp_params = self.conn_params.copy()
        temp_params["database"] = "postgres"  # Connect to default postgres database
        
        try:
            conn = psycopg2.connect(**temp_params)
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{self.conn_params['database']}'")
                exists = cursor.fetchone()
                
                if not exists:
                    cursor.execute(f"CREATE DATABASE {self.conn_params['database']}")
                    print(f"Created database {self.conn_params['database']}")
            conn.close()
        except Exception as e:
            print(f"Error creating database: {str(e)}")
    
    def init_db(self):
        """Initialize database tables if they don't exist"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                # Create scans table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    scan_id VARCHAR(36) PRIMARY KEY,
                    target TEXT NOT NULL,
                    scan_date TIMESTAMP NOT NULL,
                    status VARCHAR(20) NOT NULL
                )
                """)
                
                # Create vulnerabilities table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS vulnerabilities (
                    vuln_id SERIAL PRIMARY KEY,
                    scan_id VARCHAR(36) REFERENCES scans(scan_id),
                    source VARCHAR(10) NOT NULL,  -- 'nmap' or 'zap'
                    name TEXT NOT NULL,
                    description TEXT,
                    severity NUMERIC(3,1),
                    cvss_score NUMERIC(3,1),
                    epss_score NUMERIC(5,4),
                    risk_score NUMERIC(5,2),
                    details JSONB
                )
                """)
                
                conn.commit()
                print("Database initialized successfully")
        except Exception as e:
            conn.rollback()
            print(f"Error initializing database: {str(e)}")
        finally:
            conn.close()
    
    def save_scan_results(self, target, results):
        """Save scan results to database"""
        scan_id = str(uuid.uuid4())
        conn = self.get_connection()
        
        try:
            with conn.cursor() as cursor:
                # Insert scan record
                cursor.execute(
                    "INSERT INTO scans (scan_id, target, scan_date, status) VALUES (%s, %s, %s, %s)",
                    (scan_id, target, datetime.now(), "completed")
                )
                
                # Process vulnerabilities from nmap results
                if 'nmap' in results:
                    self._save_nmap_vulnerabilities(cursor, scan_id, results['nmap'])
                
                # Process vulnerabilities from zap results
                if 'zap' in results:
                    self._save_zap_vulnerabilities(cursor, scan_id, results['zap'])
                
                conn.commit()
                return scan_id
        except Exception as e:
            conn.rollback()
            print(f"Error saving scan results: {str(e)}")
            raise
        finally:
            conn.close()
    
    def _save_nmap_vulnerabilities(self, cursor, scan_id, nmap_results):
        """Save vulnerabilities found by Nmap"""
        if not nmap_results or 'vulnerabilities' not in nmap_results:
            return
        
        for vuln in nmap_results['vulnerabilities']:
            risk_score = vuln.get('risk_score', 0)
            
            cursor.execute(
                """
                INSERT INTO vulnerabilities 
                (scan_id, source, name, description, severity, cvss_score, epss_score, risk_score, details)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    scan_id,
                    'nmap',
                    vuln.get('name', ''),
                    vuln.get('description', ''),
                    vuln.get('severity', 0),
                    vuln.get('cvss_score', 0),
                    vuln.get('epss_score', 0),
                    risk_score,
                    json.dumps(vuln)
                )
            )
    
    def _save_zap_vulnerabilities(self, cursor, scan_id, zap_results):
        """Save vulnerabilities found by ZAP"""
        if not zap_results or 'vulnerabilities' not in zap_results:
            return
        
        for vuln in zap_results['vulnerabilities']:
            risk_score = vuln.get('risk_score', 0)
            
            cursor.execute(
                """
                INSERT INTO vulnerabilities 
                (scan_id, source, name, description, severity, cvss_score, epss_score, risk_score, details)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    scan_id,
                    'zap',
                    vuln.get('name', ''),
                    vuln.get('description', ''),
                    vuln.get('severity', 0),
                    vuln.get('cvss_score', 0),
                    vuln.get('epss_score', 0),
                    risk_score,
                    json.dumps(vuln)
                )
            )
    
    def get_all_reports(self):
        """Get list of all scan reports with summary info"""
        conn = self.get_connection()
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                SELECT s.scan_id, s.target, s.scan_date, s.status, 
                       COUNT(v.vuln_id) as vuln_count,
                       ROUND(AVG(v.risk_score), 2) as avg_risk_score,
                       MAX(v.risk_score) as max_risk_score
                FROM scans s
                LEFT JOIN vulnerabilities v ON s.scan_id = v.scan_id
                GROUP BY s.scan_id, s.target, s.scan_date, s.status
                ORDER BY s.scan_date DESC
                """)
                
                columns = [desc[0] for desc in cursor.description]
                reports = []
                
                for row in cursor.fetchall():
                    report = dict(zip(columns, row))
                    # Convert datetime to string for JSON serialization
                    report['scan_date'] = report['scan_date'].isoformat()
                    reports.append(report)
                
                return reports
        except Exception as e:
            print(f"Error getting reports: {str(e)}")
            raise
        finally:
            conn.close()
    
    def get_report(self, scan_id):
        """Get detailed report for a specific scan"""
        conn = self.get_connection()
        
        try:
            report = {"scan_info": None, "vulnerabilities": []}
            
            with conn.cursor() as cursor:
                # Get scan info
                cursor.execute(
                    "SELECT scan_id, target, scan_date, status FROM scans WHERE scan_id = %s",
                    (scan_id,)
                )
                scan_row = cursor.fetchone()
                
                if not scan_row:
                    return None
                
                scan_columns = [desc[0] for desc in cursor.description]
                report["scan_info"] = dict(zip(scan_columns, scan_row))
                report["scan_info"]["scan_date"] = report["scan_info"]["scan_date"].isoformat()
                
                # Get vulnerabilities
                cursor.execute(
                    """
                    SELECT vuln_id, source, name, description, severity, 
                           cvss_score, epss_score, risk_score, details
                    FROM vulnerabilities
                    WHERE scan_id = %s
                    ORDER BY risk_score DESC
                    """,
                    (scan_id,)
                )
                
                vuln_columns = [desc[0] for desc in cursor.description]
                
                for row in cursor.fetchall():
                    vuln = dict(zip(vuln_columns, row))
                    # Parse JSON details if it's a string, otherwise leave it as is
                    if isinstance(vuln['details'], str):
                        try:
                            vuln['details'] = json.loads(vuln['details'])
                        except (json.JSONDecodeError, TypeError) as e:
                            print(f"Warning: Could not parse details as JSON for vulnerability {vuln['vuln_id']}: {str(e)}")
                            print(f"Details type: {type(vuln['details'])}, value: {vuln['details'][:100]}")
                    report["vulnerabilities"].append(vuln)
                
                # Add summary stats
                report["summary"] = {
                    "total_vulnerabilities": len(report["vulnerabilities"]),
                    "sources": {
                        "nmap": len([v for v in report["vulnerabilities"] if v["source"] == "nmap"]),
                        "zap": len([v for v in report["vulnerabilities"] if v["source"] == "zap"])
                    },
                    "risk_levels": {
                        "critical": len([v for v in report["vulnerabilities"] if v["risk_score"] >= 9]),
                        "high": len([v for v in report["vulnerabilities"] if 7 <= v["risk_score"] < 9]),
                        "medium": len([v for v in report["vulnerabilities"] if 4 <= v["risk_score"] < 7]),
                        "low": len([v for v in report["vulnerabilities"] if v["risk_score"] < 4])
                    }
                }
                
                return report
        except Exception as e:
            print(f"Error getting report: {str(e)}")
            raise
        finally:
            conn.close()
