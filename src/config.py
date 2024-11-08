import os
from pathlib import Path


# Project structure
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
STREAM_FILE = DATA_DIR / "stream_output.jsonl"
LAST_PROCESSED_FILE = DATA_DIR / "last_processed.txt"


# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# System parameters
PARAMETERS = {
    'temperature': {
        'unit': 'Celsius',
        'expected_range': (15.0, 35.0),
        'alert_range': (10.0, 40.0),
    },
    'speed': {
        'unit': 'RPM',
        'expected_range': (1000, 2000),
        'alert_range': (800, 2200),
    },
    'status': {
        'possible_values': ['STARTED', 'RUNNING', 'PAUSED', 'COMPLETED', 'SHUTDOWN'],
        'summary_method': 'mode',
        'transitions': {
            'STARTED': ['RUNNING', 'SHUTDOWN'],
            'RUNNING': ['PAUSED', 'COMPLETED', 'SHUTDOWN'],
            'PAUSED': ['RUNNING', 'SHUTDOWN'],
            'COMPLETED': ['STARTED', 'SHUTDOWN'],
            'SHUTDOWN': ['STARTED']
        }
    }
}

# Processing settings
WINDOW_SIZE = 5
SIMULATION_INTERVAL = 1  # seconds
PROCESSING_INTERVAL = 10  # seconds
