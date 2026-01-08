"""Configuration management for AWS AI Cost Optimizer."""

import os
from typing import Optional


class Config:
    """Application configuration."""
    
    # AWS Configuration
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_ACCOUNT_ID = os.getenv('AWS_ACCOUNT_ID')
    
    # S3 Configuration
    S3_BUCKET = os.getenv('S3_BUCKET', 'aws-cost-optimizer-data')
    S3_PREFIX = os.getenv('S3_PREFIX', '')
    
    # DynamoDB Configuration
    DYNAMODB_TABLE = os.getenv('DYNAMODB_TABLE', 'cost-optimizer-summaries')
    
    # Data Collection Settings
    COST_COLLECTION_DAYS = int(os.getenv('COST_COLLECTION_DAYS', '90'))
    METRICS_COLLECTION_DAYS = int(os.getenv('METRICS_COLLECTION_DAYS', '15'))
    METRICS_PERIOD_SECONDS = int(os.getenv('METRICS_PERIOD_SECONDS', '3600'))
    
    # CloudWatch Metrics Configuration
    MIN_RESOURCE_AGE_DAYS = int(os.getenv('MIN_RESOURCE_AGE_DAYS', '15'))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def get_s3_path(cls, prefix: str) -> str:
        """Get full S3 path with prefix."""
        if cls.S3_PREFIX:
            return f"{cls.S3_PREFIX}/{prefix}"
        return prefix
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration."""
        if not cls.S3_BUCKET:
            raise ValueError("S3_BUCKET must be configured")
        return True
