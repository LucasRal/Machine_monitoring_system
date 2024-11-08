import json
import time
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from config import PARAMETERS, SIMULATION_INTERVAL, STREAM_FILE
from utils import setup_logger

logger = setup_logger("simulator")

class MachineSimulator:
    def __init__(self, output_file: Path):
        self.output_file = output_file
        self.running = False
        self.current_status = 'SHUTDOWN'  # Set the initial state as shutdown
    
    def get_next_status(self) -> str:
        """Determine next status based on current status and valid transitions."""
        valid_transitions = PARAMETERS['status']['transitions'][self.current_status]

        if self.current_status == 'SHUTDOWN':
            # Always go to STARTED from SHUTDOWN
            return 'STARTED'
        elif self.current_status == 'STARTED':
            # Usually progress to RUNNING
            return 'RUNNING' if random.random() < 0.9 else 'SHUTDOWN'
        elif self.current_status == 'RUNNING':
            # Small chance to change status in the valid status transition
            if random.random() < 0.1:
                possible_next = [s for s in valid_transitions if s != self.current_status]
                return random.choice(possible_next)
            return 'RUNNING'
        elif self.current_status == 'PAUSED':
            # Usually resume running, but Shuting down is also a possible transition
            return 'RUNNING' if random.random() < 0.8 else 'SHUTDOWN'
        elif self.current_status == 'COMPLETED':
            # Start new cycle or shutdown
            return 'STARTED' if random.random() < 0.7 else 'SHUTDOWN'
        
        return self.current_status

    def generate_reading(self) -> Dict[str, Any]:
        """Generate a single machine reading."""
        # Update status
        new_status = self.get_next_status()
        self.current_status = new_status
        
        # Generate temperature and speed based on status
        if new_status == 'SHUTDOWN':
            temp = random.uniform(15.0, 20.0)  # Cooler when shutdown
            speed = 0
        elif new_status == 'PAUSED':
            temp = random.uniform(20.0, 25.0)
            speed = random.uniform(800, 1000)  # Lower speed when paused
        elif new_status in ['RUNNING', 'STARTED']:
            temp = random.uniform(25.0, 35.0)  # Warmer when running
            speed = random.uniform(1000, 2000)
        else:  # COMPLETED
            temp = random.uniform(20.0, 30.0)
            speed = random.uniform(800, 1200)  # Slowing down
            
        return {
            "timestamp": datetime.now().isoformat(),
            "temperature": round(temp, 2),
            "speed": round(speed, 2),
            "status": new_status
        }

    def write_reading(self, reading: Dict[str, Any]):
        """Write reading to both file and stdout."""
        with self.output_file.open('a') as f:
            json_line = json.dumps(reading)
            f.write(json_line + '\n')
            print(f"{json_line}")
    
    def run(self):
        """Run the simulation continuously."""
        self.running = True
        logger.info("Starting machine simulation...")
        
        try:
            while self.running:
                reading = self.generate_reading()
                self.write_reading(reading)
                time.sleep(SIMULATION_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Stopping machine simulation...")
            self.running = False
        except Exception as e:
            logger.error(f"Error in simulation: {str(e)}", exc_info=True)
            self.running = False

if __name__ == "__main__":
    output_path = Path(STREAM_FILE)
    simulator = MachineSimulator(output_path)
    simulator.run()