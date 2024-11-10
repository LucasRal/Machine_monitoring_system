import pandas as pd
import json
from typing import Dict, Union, Optional, List, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Anomaly:
    """Data class to store anomaly information."""
    timestamp: datetime
    value: float
    deviation_percentage: float

class DataAnalyzer:
    """A class to analyze machine monitoring data with anomaly detection."""
    
    def __init__(self, data_path: Union[str, Path], anomaly_threshold: float = 20.0):
        """
        Initialize the DataAnalyzer with a path to the JSON data file.
        
        Args:
            data_path (Union[str, Path]): Path to the JSON data file
            anomaly_threshold (float): Percentage threshold for anomaly detection (default: 20.0)
        """
        self.data_path = Path(data_path)
        self.anomaly_threshold = anomaly_threshold
        self.df = self._load_data()
    
    def _load_data(self) -> pd.DataFrame:
        """
        Load and preprocess the JSON data file where each line is a separate JSON object.
        
        Returns:
            pd.DataFrame: Processed DataFrame with parsed timestamps
        """
        try:
            # Read JSON file line by line
            data = []
            with open(self.data_path, 'r') as file:
                for line in file:
                    if line.strip():  # Skip empty lines
                        data.append(json.loads(line.strip()))
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Convert timestamp to datetime while preserving ISO format
            df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
            
            return df
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Data file not found at: {self.data_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in data file: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Error loading data: {str(e)}")

    def detect_anomalies(self, metric: str) -> List[Anomaly]:
        """
        Detect anomalies in the specified metric based on deviation from mean.
        
        Args:
            metric (str): The metric to analyze (e.g., 'speed', 'temperature')
            
        Returns:
            List[Anomaly]: List of detected anomalies with their details
        """
        if metric not in self.df.columns:
            raise ValueError(f"Metric '{metric}' not found in data")

        mean_value = self.df[metric].mean()
        anomalies = []

        for _, row in self.df.iterrows():
            value = row[metric]
            deviation = abs(value - mean_value)
            deviation_percentage = (deviation / mean_value) * 100

            if deviation_percentage > self.anomaly_threshold:
                anomaly = Anomaly(
                    timestamp=row['timestamp'],
                    value=value,
                    deviation_percentage=round(deviation_percentage, 2)
                )
                anomalies.append(anomaly)

        return anomalies

    def analyze_metric(self, metric: str) -> Dict[str, Union[float, int, List[Dict]]]:
        """
        Calculate statistics and detect anomalies for a given metric.
        
        Args:
            metric (str): The metric to analyze (e.g., 'speed', 'temperature')
            
        Returns:
            Dict: Dictionary containing statistics and anomalies
        """
        if metric not in self.df.columns:
            raise ValueError(f"Metric '{metric}' not found in data")
        
        try:
            # Calculate basic statistics
            stats = {
                'average': round(self.df[metric].mean(), 2),
                'maximum': round(self.df[metric].max(), 2),
                'minimum': round(self.df[metric].min(), 2),
                'data_points': len(self.df),
            }
            
            # Detect anomalies
            anomalies = self.detect_anomalies(metric)
            stats['anomalies'] = [
                {
                    'timestamp': anomaly.timestamp.isoformat(),  # Use ISO format
                    'value': round(anomaly.value, 2),
                    'deviation_percentage': anomaly.deviation_percentage
                }
                for anomaly in anomalies
            ]
            stats['anomaly_count'] = len(anomalies)
            
            return stats
            
        except Exception as e:
            raise RuntimeError(f"Error analyzing data: {str(e)}")

def format_metric_value(value: float, metric: str) -> str:
    """Format metric value with appropriate unit."""
    return f"{value}{'°C' if metric == 'temperature' else ' units'}"

def main():
    try:
        # Initialize analyzer with 20% threshold (by default) for anomalies
        analyzer = DataAnalyzer('data/stream_output.jsonl', anomaly_threshold=20.0)
        
        # Analyze metrics
        for metric in ['speed', 'temperature']:
            stats = analyzer.analyze_metric(metric)
            
            print(f"\n{metric.capitalize()} Statistics:")
            print(f"Average: {format_metric_value(stats['average'], metric)}")
            print(f"Maximum: {format_metric_value(stats['maximum'], metric)}")
            print(f"Minimum: {format_metric_value(stats['minimum'], metric)}")
            print(f"Number of readings: {stats['data_points']}")
            
            # Report anomalies
            print(f"\nAnomalies detected: {stats['anomaly_count']}")
            if stats['anomalies']:
                print("\nDetailed Anomalies:")
                for anomaly in stats['anomalies']:
                    print(f"Timestamp: {anomaly['timestamp']}")
                    print(f"Value: {format_metric_value(anomaly['value'], metric)}")
                    print(f"Deviation: {anomaly['deviation_percentage']}%")
                    print("-" * 50)
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()