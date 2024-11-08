# Machine Monitoring System

A Python-based system for simulating and monitoring machine data with real-time processing and REST API capabilities.

## Overview
The system simulates a machine generating sensor data (temperature, speed, status), processes this data in real-time, and provides API access to the machine's state and processed metrics.

## Features

### Data Simulation
- Generates realistic machine sensor data:
  - Temperature readings (15.0-35.0°C normal range)
  - Speed measurements (1000-2000 RPM normal range)
  - Machine status transitions (STARTED → RUNNING → PAUSED → COMPLETED → SHUTDOWN)
- Outputs to console and JSONL file
- 2-second simulation interval

### Real-time Processing
- 10-second processing interval
- Moving average calculations using numpy
- Health score generation
- CSV output for processed data
- Timestamp-based duplicate prevention

### REST API
- `GET /data`: Latest processed machine data
- `GET /status`: Current machine status
- `POST /status`: Update machine status with validation
- Status transition validation
- Error handling and logging

## Project Structure
```bash
machine_monitoring/
├── src/
│   ├── __init__.py
│   ├── simulator.py        # Data streaming simulation
│   ├── processor.py        # Data processing logic
│   ├── api.py             # REST API implementation
│   ├── config.py          # Configuration parameters
│   └── utils.py           # Shared utilities
├── data/                  # Data storage directory
│   ├── stream_output.jsonl # Raw streaming data
│   ├── analysis_output.csv # Processed data
│   └── last_processed.txt  # Processing checkpoint
├── logs/                  # Log files directory
├── requirements.txt       # Project dependencies
├── setup.py              # Package configuration
├── run.py                # Main simulation script
└── run_api.py            # API server script
```

## Installation

1. Clone the repository
```bash
git clone <repository-url>
cd machine_monitoring
```

2. Create and activate virtual environment
 ```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install package
```bash
pip install -e .
```

## Usage

### Simulation

Run complete system (simulator + processor):

```bash
python run.py
```

Run individual components:
```bash
python run.py --simulator-only  # Run only simulator
python run.py --processor-only  # Run only processor
```

### API Server

Start the server:

python run_api.py

API Examples:

# Get latest processed data
```bash
curl http://localhost:5000/data
```
**<ins>Example Output:</ins>:**
```bash
{
  "current_status": "COMPLETED",  # Current (latest) status in the streaming output
  "processed_data": {
    "alerts": "Machine paused - may require attention",
    "health_score": 0.52,
    "speed_current": 901.2,
    "speed_moving_avg": 1342.8480000000002,
    "speed_trend": "decreasing",
    "status_changes": 3,
    "status_current": "PAUSED", # Most recent status in the processed reading window data
    "status_mode_in_window": "RUNNING",
    "temperature_current": 22.14,
    "temperature_moving_avg": 28.178,
    "temperature_trend": "decreasing",
    "timestamp": "2024-11-08T14:37:57.750393"
  },
  "success": true,
  "timestamp": "2024-11-08T15:09:21.746969"
}
```

# Get current machine status
```bash
curl http://localhost:5000/status
```
**<ins>Example Output</ins>:**
```bash
{
  "data": {
    "speed": 901.2,
    "status": "COMPLETED",
    "temperature": 22.14,
    "timestamp": "2024-11-08T15:09:21.746969"
  },
  "success": true
}
```

# Update machine status
**<ins>Note</ins>:** The request will respond with an error if the status transition is not valid. 
To see the valid transitions between statuses, see the config.py file.
```bash
curl -X POST http://localhost:5000/status \
     -H "Content-Type: application/json" \
     -d '{"status": "STARTED"}'
```
- **<ins>Example Output for valid status transition</ins>:**
```bash
{
	"success": true,
	"data": {
		"timestamp": "2024-11-08T15:26:38.361401",
		"temperature": 22.14,
		"speed": 901.2,
		"status": "COMPLETED"
	}
}
```
- **<ins>Example Output for non-valid status transition</ins>:**
```bash
{
	"success": false,
	"error": "Invalid status transition from COMPLETED to PAUSED"
}
```


## Data Formats

### Streaming Output (JSONL)
```bash
{"timestamp": "2024-11-08T10:15:23.456789", "temperature": 25.7, "speed": 1500, "status": "RUNNING"}
```

### Processed Output (CSV)
Columns:
- timestamp: Data timestamp
- temperature_current: Current temperature
- temperature_moving_avg: Moving average temperature
- temperature_trend: Temperature trend (stable/increasing/decreasing)
- speed_current: Current speed
- speed_moving_avg: Moving average speed
- speed_trend: Speed trend
- status_current: Current machine status
- status_mode: Most frequent status in window
- status_changes: Number of status changes
- health_score: Overall machine health (0-1)
- alerts: Any active alerts

## Configuration

Key parameters (`config.py`):
- SIMULATION_INTERVAL: 2 seconds
- PROCESSING_INTERVAL: 10 seconds
- WINDOW_SIZE: 5 readings
- Temperature ranges:
  - Normal: 15.0-35.0°C
  - Alert: 10.0-40.0°C
- Speed ranges:
  - Normal: 1000-2000 RPM
  - Alert: 800-2200 RPM

## Dependencies

- numpy: Numerical computations
- pandas: Data processing & CSV handling
- flask: REST API
- python-json-logger: Structured logging
- python-dotenv: Configuration management

## Logging

System logs are stored in `logs/`:
- simulator.log: Simulation events
- processor.log: Data processing events
- api.log: API server events

All logs include timestamps, log levels, and relevant context.

## Error Handling

- Status transition validation
- Missing/corrupted file handling
- Detailed API error responses
- Timestamped error logging