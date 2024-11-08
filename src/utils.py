import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from pythonjsonlogger import jsonlogger
import numpy as np
from typing import List, Dict, Any, Optional
from src.config import LOGS_DIR


def setup_logger(name: str) -> logging.Logger:
    """Configure JSON logging with rotation."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Console logs handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(jsonlogger.JsonFormatter())
    logger.addHandler(console_handler)
    
    # File logs handler
    file_handler = RotatingFileHandler(
        LOGS_DIR / f"{name}.log",
        maxBytes=1024*1024,
        backupCount=5
    )
    file_handler.setFormatter(jsonlogger.JsonFormatter())
    logger.addHandler(file_handler)
    
    return logger


def calculate_moving_stats(values: np.ndarray, window_size: int = 5) -> Dict[str, Any]:
    """Calculate moving average for numerical data."""
    if len(values) == 0:
        return {
            "moving_avg": np.nan,
            "trend": "insufficient_data"
        }
        
    # Pad with edge values for initial window (0 until the fourth window)
    padded = np.pad(values, (window_size-1, 0), mode='edge')
    
    # Calculate moving average
    moving_avg = np.convolve(padded, np.ones(window_size)/window_size, mode='valid')[-1]
    
    # Calculate trend
    if len(values) >= 2:
        slope = values[-1] - values[-2]
        if abs(slope) < 0.1:  # Threshold for stability
            trend = "stable"
        elif slope > 0:
            trend = "increasing"
        else:
            trend = "decreasing"
    else:
        trend = "stable"
    
    return {
        "moving_avg": float(moving_avg),
        "trend": trend
    }
