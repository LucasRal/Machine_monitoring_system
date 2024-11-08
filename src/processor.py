import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

from config import (
    PARAMETERS, PROCESSING_INTERVAL, WINDOW_SIZE,
    STREAM_FILE, LAST_PROCESSED_FILE
)
from utils import setup_logger, calculate_moving_stats

logger = setup_logger("processor")


class DataProcessor:
    def __init__(self, 
                 input_file: Path,
                 last_processed_file: Path,
                 window_size: int = WINDOW_SIZE):
        self.input_file = input_file
        self.last_processed_file = last_processed_file
        self.window_size = window_size
        self.running = False
        
        # Initialize data buffers
        self.temp_buffer: List[float] = []
        self.speed_buffer: List[float] = []
        self.status_buffer: List[str] = []

        # Load last processed timestamp
        self.last_processed = self.load_last_processed()

    
    def load_last_processed(self) -> Optional[datetime]:
        """Load the last processed timestamp from file."""
        try:
            if self.last_processed_file.exists():
                timestamp_str = self.last_processed_file.read_text().strip()
                return datetime.fromisoformat(timestamp_str)
        except Exception as e:
            logger.error(f"Error loading last processed timestamp: {e}")
        return None

    
    def save_last_processed(self, timestamp: datetime):
        """Save the last processed timestamp to file."""
        try:
            self.last_processed_file.write_text(timestamp.isoformat())
        except Exception as e:
            logger.error(f"Error saving last processed timestamp: {e}")

    
    def process_new_readings(self) -> List[Dict[str, Any]]:
        """Process new readings from the input file."""
        new_readings = []
        
        try:
            with self.input_file.open('r') as f:
                for line in f:
                    reading = json.loads(line.strip())
                    timestamp = datetime.fromisoformat(reading['timestamp'])
                    
                    if self.last_processed and timestamp <= self.last_processed:
                        continue
                        
                    new_readings.append(reading)
                    self.last_processed = timestamp
        except Exception as e:
            logger.error(f"Error reading new data: {e}")
            
        return new_readings


    def update_buffers(self, readings: List[Dict[str, Any]]):
        """Update data buffers with new readings."""
        for reading in readings:
            self.temp_buffer.append(reading['temperature'])
            self.speed_buffer.append(reading['speed'])
            self.status_buffer.append(reading['status'])
            
            # Keep only window_size elements
            self.temp_buffer = self.temp_buffer[-self.window_size:]
            self.speed_buffer = self.speed_buffer[-self.window_size:]
            self.status_buffer = self.status_buffer[-self.window_size:]


    def calculate_health_score(self, current_reading: Dict[str, Any]) -> float:
        """Calculate overall health score based on all parameters."""
        # Base scores from temperature and speed
        temp_score = max(0, 1 - abs(current_reading['temperature'] - 25) / 15)
        speed_score = max(0, 1 - abs(current_reading['speed'] - 1500) / 700)
        
        # Status score
        status_scores = {
            'STARTED': 0.8,   # Starting up - good
            'RUNNING': 1.0,   # Running - optimal
            'PAUSED': 0.6,    # Paused - not optimal but not bad
            'COMPLETED': 0.9, # Completed - good
            'SHUTDOWN': 0.5   # Shutdown - not optimal but might be intended
        }
        status_score = status_scores.get(current_reading['status'], 0.5)
        
        return round((temp_score + speed_score + status_score) / 3, 2)


    def process_and_analyze(self) -> Optional[Dict[str, Any]]:
        """Process recent readings and generate analysis."""
        readings = self.process_new_readings()
        if not readings:
            return None
            
        self.update_buffers(readings)
        current_reading = readings[-1]
        
        # Convert lists to numpy arrays for calculations
        temp_array = np.array(self.temp_buffer)
        speed_array = np.array(self.speed_buffer)
        
        temp_stats = calculate_moving_stats(temp_array, self.window_size)
        speed_stats = calculate_moving_stats(speed_array, self.window_size)
        
        # Calculate status mode
        status_mode = max(set(self.status_buffer), key=self.status_buffer.count)

        analysis = {
            "timestamp": current_reading['timestamp'],
            "window_stats": {
                "temperature": {
                    "current": current_reading['temperature'],
                    "moving_avg": temp_stats['moving_avg'],
                    "is_outlier": not (
                        PARAMETERS['temperature']['expected_range'][0]
                        <= current_reading['temperature']
                        <= PARAMETERS['temperature']['expected_range'][1]
                    ),
                    "trend": temp_stats['trend']
                },
                "speed": {
                    "current": current_reading['speed'],
                    "moving_avg": speed_stats['moving_avg'],
                    "is_outlier": not (
                        PARAMETERS['speed']['expected_range'][0]
                        <= current_reading['speed']
                        <= PARAMETERS['speed']['expected_range'][1]
                    ),
                    "trend": speed_stats['trend']
                },
                "status": {
                    "current": current_reading['status'],
                    "mode": status_mode,
                    "changes_in_window": len(set(self.status_buffer))
                }
            },
            "analysis": {
                "health_score": self.calculate_health_score(current_reading),
                "alerts": self.generate_alerts(current_reading)
            }
        }
        
        return analysis


    def generate_alerts(self, reading: Dict[str, Any]) -> List[str]:
        """Generate alerts based on current readings."""
        alerts = []
        
        # Temperature and speed alerts
        if not (PARAMETERS['temperature']['alert_range'][0]
                <= reading['temperature']
                <= PARAMETERS['temperature']['alert_range'][1]):
            alerts.append(f"Temperature out of safe range: {reading['temperature']}")
            
        if not (PARAMETERS['speed']['alert_range'][0]
                <= reading['speed']
                <= PARAMETERS['speed']['alert_range'][1]):
            alerts.append(f"Speed out of safe range: {reading['speed']}")
        
        # Status-specific alerts
        if reading['status'] == 'PAUSED':
            alerts.append("Machine paused - may require attention")
        elif reading['status'] == 'SHUTDOWN':
            alerts.append("Machine shutdown - check if scheduled")
        
        return alerts


    def run(self):
        """Run the processor continuously."""
        self.running = True
        logger.info("Starting data processor...")
        
        try:
            while self.running:
                analysis = self.process_and_analyze()
                if analysis:
                    print(json.dumps(analysis, indent=2))
                    self.save_last_processed(datetime.fromisoformat(analysis['timestamp']))
                time.sleep(PROCESSING_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Stopping data processor...")
            self.running = False
        except Exception as e:
            logger.error(f"Error in processor: {str(e)}", exc_info=True)
            self.running = False


if __name__ == "__main__":
    processor = DataProcessor(input_file=STREAM_FILE, last_processed_file=LAST_PROCESSED_FILE)
    processor.run()