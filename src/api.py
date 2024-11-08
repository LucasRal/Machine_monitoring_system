from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from typing import Dict, Any, Optional
from datetime import datetime
import pandas as pd
import json
from pathlib import Path

from src.config import PARAMETERS, ANALYSIS_CSV, STREAM_FILE

app = Flask(__name__)
api = Api(app)


def get_latest_stream_data() -> Optional[Dict[str, Any]]:
    """Read the latest data from the stream file."""
    try:
        if not STREAM_FILE.exists():
            return None
            
        last_line = STREAM_FILE.read_text().strip().split('\n')[-1]
        return json.loads(last_line)
            
    except Exception as e:
        app.logger.error(f"Error reading stream file: {e}")
        return None

class MachineDataResource(Resource):
    def get(self):
        """Return the latest processed machine data."""
        try:
            # Get current status from stream file
            current_data = get_latest_stream_data()
            current_status = current_data['status'] if current_data else None
            
            # Get processed data from CSV
            if Path(ANALYSIS_CSV).exists():
                df = pd.read_csv(ANALYSIS_CSV)
                if not df.empty:
                    latest_data = df.iloc[-1].to_dict()
                    return jsonify({
                        "success": True,
                        "processed_data": latest_data,
                        "current_status": current_status,
                        "timestamp": current_data['timestamp'] if current_data else None
                    })
            
            return jsonify({
                "success": False,
                "error": "No data available",
                "current_status": current_status,
                "timestamp": current_data['timestamp'] if current_data else None
            })
        
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

class MachineStatusResource(Resource):
    def get(self):
        """Return the current machine status from stream file."""
        current_data = get_latest_stream_data()
        
        if current_data:
            return jsonify({
                "success": True,
                "data": {
                    "status": current_data['status'],
                    "timestamp": current_data['timestamp'],
                    "temperature": current_data['temperature'],
                    "speed": current_data['speed']
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "No current data available"
            }), 404
    
    def post(self):
        """Update machine status."""
        try:
            data = request.get_json()
            
            if not data or 'status' not in data:
                return {
                    "success": False,
                    "error": "Status is required"
                }, 400
            
            new_status = data['status'].upper()
            
            # Validate status
            if new_status not in PARAMETERS['status']['possible_values']:
                return {
                    "success": False,
                    "error": f"Invalid status. Allowed values: {PARAMETERS['status']['possible_values']}"
                }, 400
            
            # Get current status from stream
            current_data = get_latest_stream_data()
            if not current_data:
                return {
                    "success": False,
                    "error": "Cannot update status: no current data available"
                }, 400
                
            current_status = current_data['status']
            
            # Validate status transition
            valid_transitions = PARAMETERS['status']['transitions'].get(current_status, [])
            if new_status != current_status and new_status not in valid_transitions:
                return {
                    "success": False,
                    "error": f"Invalid status transition from {current_status} to {new_status}"
                }, 400
            
            # Create new data entry
            new_data = {
                "timestamp": datetime.now().isoformat(),
                "temperature": current_data['temperature'],
                "speed": current_data['speed'],
                "status": new_status
            }
            
            # Append to stream file
            with STREAM_FILE.open('a') as f:
                f.write(json.dumps(new_data) + '\n')
            
            return {
                "success": True,
                "data": new_data
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }, 500

# Register resources
api.add_resource(MachineDataResource, '/data')
api.add_resource(MachineStatusResource, '/status')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Resource not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
