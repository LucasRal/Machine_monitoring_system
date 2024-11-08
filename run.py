import argparse
import multiprocessing
from pathlib import Path
from src.simulator import MachineSimulator
from src.processor import DataProcessor
from src.config import STREAM_FILE, LAST_PROCESSED_FILE


def run_simulator(output_file: Path):
    simulator = MachineSimulator(output_file)
    simulator.run()

def run_processor(input_file: Path, last_processed_file: Path):
    processor = DataProcessor(input_file, last_processed_file)
    processor.run()

def main():
    parser = argparse.ArgumentParser(description='Run machine monitoring system')
    parser.add_argument('--simulator-only', action='store_true',
                       help='Run only the simulator')
    parser.add_argument('--processor-only', action='store_true',
                       help='Run only the processor')
    
    args = parser.parse_args()
    
    if args.simulator_only:
        run_simulator(STREAM_FILE)
    elif args.processor_only:
        run_processor(STREAM_FILE, LAST_PROCESSED_FILE)
    else:
        # Run both simulator and processor in parallel
        simulator_process = multiprocessing.Process(
            target=run_simulator,
            args=(STREAM_FILE,)
        )
        processor_process = multiprocessing.Process(
            target=run_processor,
            args=(STREAM_FILE, LAST_PROCESSED_FILE)
        )
        
        simulator_process.start()
        processor_process.start()
        
        try:
            simulator_process.join()
            processor_process.join()
        except KeyboardInterrupt:
            simulator_process.terminate()
            processor_process.terminate()
            simulator_process.join()
            processor_process.join()

if __name__ == "__main__":
    main()
