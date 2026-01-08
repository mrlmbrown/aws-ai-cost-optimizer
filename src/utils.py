"""Utility functions for AWS AI Cost Optimizer."""

import logging
import sys
from datetime import datetime, timedelta
from typing import List, Tuple


def setup_logging(log_level: str = 'INFO') -> None:
    """Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def get_date_ranges(days_back: int, chunk_days: int = 30) -> List[Tuple[str, str]]:
    """Generate date ranges for API calls with chunking.
    
    CloudWatch API limits require chunking large date ranges.
    
    Args:
        days_back: Total number of days to go back
        chunk_days: Size of each chunk in days
        
    Returns:
        List of (start_date, end_date) tuples
    """
    end_date = datetime.utcnow().date()
    ranges = []
    
    current_end = end_date
    days_remaining = days_back
    
    while days_remaining > 0:
        chunk_size = min(chunk_days, days_remaining)
        current_start = current_end - timedelta(days=chunk_size)
        
        ranges.append((
            current_start.isoformat(),
            current_end.isoformat()
        ))
        
        current_end = current_start
        days_remaining -= chunk_size
    
    return list(reversed(ranges))


def calculate_cost_per_hour(monthly_cost: float) -> float:
    """Convert monthly cost to hourly cost.
    
    Args:
        monthly_cost: Monthly cost in dollars
        
    Returns:
        Hourly cost in dollars
    """
    # Assume 730 hours per month (365 days * 24 hours / 12 months)
    return monthly_cost / 730


def format_bytes(bytes_value: float) -> str:
    """Format bytes to human-readable string.
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        Formatted string (e.g., '1.5 GB')
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def calculate_utilization_score(cpu_avg: float, memory_avg: float,
                               network_avg: float = 0) -> float:
    """Calculate overall utilization score.
    
    Args:
        cpu_avg: Average CPU utilization (0-100)
        memory_avg: Average memory utilization (0-100)
        network_avg: Average network utilization (0-100)
        
    Returns:
        Weighted utilization score (0-100)
    """
    # Weighted average: CPU 50%, Memory 40%, Network 10%
    score = (cpu_avg * 0.5) + (memory_avg * 0.4) + (network_avg * 0.1)
    return min(100, max(0, score))
