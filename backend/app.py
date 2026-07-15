from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import json
import sys
import threading
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules
from backend.scanner.nmap_scanner import NmapScanner
from backend.scanner.zap_scanner import ZapScanner
from backend.risk_assessment.risk_engine import RiskEngine
from backend.database.db_handler import DatabaseHandler

app = Flask(__name__, static_folder="../frontend", template_folder="../frontend")
CORS(app)

# Set secret key from environment
app.secret_key = os.getenv("FLASK_SECRET_KEY", "vulnshield_dev_key")

# Initialize components
db_handler = DatabaseHandler()
nmap_scanner = NmapScanner()
zap_scanner = ZapScanner(zap_path=os.getenv("ZAP_PATH"))
risk_engine = RiskEngine()

# Store active scans
active_scans = {}

def run_scan(scan_id, target, scan_type):
    """Run scan in background thread"""
    try:
        results = {}
        progress = 0
        
        # Update scan status
        active_scans[scan_id].update({
            'status': 'running',
            'progress': progress,
            'message': 'Starting scan...'
        })
        
        # Run NMAP scan if requested
        if scan_type in ['nmap', 'both']:
            active_scans[scan_id].update({
                'message': 'Running NMAP vulnerability scan...',
                'progress': 20
            })
            nmap_results = nmap_scanner.run_scan(target)
            results['nmap'] = nmap_results
            progress = 50
        
        # Run ZAP CLI scan if requested
        if scan_type in ['zap', 'both']:
            active_scans[scan_id].update({
                'progress': 50,
                'message': 'Running ZAP vulnerability scan... This may take some time to complete thoroughly.'
            })
            # Run ZAP scan with no timeout to ensure it completes
            zap_results = zap_scanner.run_scan(target)
            results['zap'] = zap_results
        
        # Process results through risk engine
        if results:
            active_scans[scan_id].update({
                'message': 'Calculating risk scores...',
                'progress': 90
            })
            risk_scores = risk_engine.calculate_risk(results)
            results['risk_scores'] = risk_scores
            
            # Save results to database
            db_handler.save_scan_results(target, results)
        
        # Mark scan as completed
        active_scans[scan_id].update({
            'status': 'completed',
            'progress': 100,
            'message': 'Scan completed successfully',
            'completed_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        # Update scan status on error
        active_scans[scan_id].update({
            'status': 'error',
            'message': str(e),
            'completed_at': datetime.now().isoformat()
        })

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('../frontend/js', path)

@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('../frontend/css', path)

@app.route('/api/scan', methods=['POST'])
def start_scan():
    data = request.json
    target = data.get('target')
    scan_type = data.get('scan_type', 'both')  # nmap, zap, or both
    
    if not target:
        return jsonify({"error": "Target is required"}), 400
    
    # Generate unique scan ID
    scan_id = str(uuid.uuid4())
    
    # Initialize scan status
    active_scans[scan_id] = {
        'target': target,
        'scan_type': scan_type,
        'status': 'initializing',
        'progress': 0,
        'message': 'Initializing scan...',
        'started_at': datetime.now().isoformat()
    }
    
    # Start scan in background thread
    thread = threading.Thread(target=run_scan, args=(scan_id, target, scan_type))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "status": "success",
        "scan_id": scan_id,
        "message": "Scan started successfully"
    })

@app.route('/api/scan/<scan_id>/status', methods=['GET'])
def get_scan_status(scan_id):
    """Get status of a running scan"""
    if scan_id not in active_scans:
        return jsonify({
            "status": "error",
            "message": "Scan not found"
        }), 404
    
    scan_info = active_scans[scan_id]
    
    # Clean up completed scans older than 1 hour
    if scan_info.get('completed_at'):
        completed_time = datetime.fromisoformat(scan_info['completed_at'])
        if (datetime.now() - completed_time).total_seconds() > 3600:
            del active_scans[scan_id]
    
    return jsonify(scan_info)

@app.route('/api/reports', methods=['GET'])
def get_reports():
    try:
        reports = db_handler.get_all_reports()
        return jsonify(reports)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/report/<scan_id>', methods=['GET'])
def get_report(scan_id):
    try:
        report = db_handler.get_report(scan_id)
        if report:
            return jsonify(report)
        return jsonify({"error": "Report not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Ensure database is initialized
    print("Initializing database...")
    db_handler.init_db()
    
    # Verify database connection and tables
    try:
        reports = db_handler.get_all_reports()
        print(f"Database connection verified. Found {len(reports)} existing reports.")
    except Exception as e:
        print(f"WARNING: Could not verify database: {str(e)}")
        print("The application will continue, but database operations may fail.")
    
    app.run(
        debug=os.getenv("FLASK_ENV", "production") == "development",
        host='0.0.0.0', 
        port=int(os.getenv("PORT", 5000))
    )
