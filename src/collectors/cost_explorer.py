"""Cost Explorer data collection module.

Collects AWS cost and usage data using the Cost Explorer API,
stores raw data in S3 and processed summaries in DynamoDB.
"""

import boto3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class CostExplorerCollector:
    """Collects cost data from AWS Cost Explorer API."""
    
    def __init__(self, region: str = 'us-east-1', s3_bucket: Optional[str] = None,
                 dynamodb_table: Optional[str] = None):
        """Initialize Cost Explorer collector.
        
        Args:
            region: AWS region for Cost Explorer API (must be us-east-1)
            s3_bucket: S3 bucket for raw data storage
            dynamodb_table: DynamoDB table for cost summaries
        """
        self.ce_client = boto3.client('ce', region_name='us-east-1')  # CE only in us-east-1
        self.s3_client = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.s3_bucket = s3_bucket
        self.dynamodb_table = dynamodb_table
        
    def fetch_cost_data(self, start_date: str, end_date: str, 
                        granularity: str = 'DAILY',
                        group_by: Optional[List[Dict]] = None) -> Dict:
        """Fetch cost and usage data from Cost Explorer.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            granularity: DAILY, MONTHLY, or HOURLY
            group_by: List of grouping dimensions
            
        Returns:
            Dict containing cost and usage data
        """
        if group_by is None:
            group_by = [
                {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                {'Type': 'DIMENSION', 'Key': 'RESOURCE_ID'}
            ]
            
        try:
            logger.info(f"Fetching cost data from {start_date} to {end_date}")
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={'Start': start_date, 'End': end_date},
                Granularity=granularity,
                Metrics=['AmortizedCost', 'UsageQuantity', 'UnblendedCost'],
                GroupBy=group_by,
                Filter={
                    'Dimensions': {
                        'Key': 'RECORD_TYPE',
                        'Values': ['Usage']
                    }
                }
            )
            logger.info(f"Retrieved {len(response.get('ResultsByTime', []))} time periods")
            return response
            
        except Exception as e:
            logger.error(f"Error fetching cost data: {str(e)}")
            raise
    
    def fetch_cost_forecast(self, start_date: str, end_date: str,
                           metric: str = 'UNBLENDED_COST') -> Dict:
        """Fetch cost forecast from Cost Explorer.
        
        Args:
            start_date: Forecast start date
            end_date: Forecast end date
            metric: Cost metric to forecast
            
        Returns:
            Dict containing forecast data
        """
        try:
            logger.info(f"Fetching cost forecast from {start_date} to {end_date}")
            response = self.ce_client.get_cost_forecast(
                TimePeriod={'Start': start_date, 'End': end_date},
                Metric=metric,
                Granularity='MONTHLY'
            )
            return response
            
        except Exception as e:
            logger.error(f"Error fetching cost forecast: {str(e)}")
            raise
    
    def store_to_s3(self, data: Dict, date_str: str) -> str:
        """Store raw cost data to S3.
        
        Args:
            data: Cost data dictionary
            date_str: Date string for partitioning
            
        Returns:
            S3 object key
        """
        if not self.s3_bucket:
            raise ValueError("S3 bucket not configured")
            
        key = f"raw/cost-explorer/year={date_str[:4]}/month={date_str[5:7]}/day={date_str[8:10]}/data.json"
        
        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=key,
                Body=json.dumps(data, default=str),
                ContentType='application/json'
            )
            logger.info(f"Stored cost data to s3://{self.s3_bucket}/{key}")
            return key
            
        except Exception as e:
            logger.error(f"Error storing to S3: {str(e)}")
            raise
    
    def store_to_dynamodb(self, summary_data: Dict) -> None:
        """Store cost summary to DynamoDB.
        
        Args:
            summary_data: Processed cost summary
        """
        if not self.dynamodb_table:
            raise ValueError("DynamoDB table not configured")
            
        table = self.dynamodb.Table(self.dynamodb_table)
        
        # Convert floats to Decimal for DynamoDB
        def convert_floats(obj):
            if isinstance(obj, float):
                return Decimal(str(obj))
            elif isinstance(obj, dict):
                return {k: convert_floats(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_floats(i) for i in obj]
            return obj
        
        try:
            table.put_item(Item=convert_floats(summary_data))
            logger.info(f"Stored summary to DynamoDB: {summary_data.get('date')}")
            
        except Exception as e:
            logger.error(f"Error storing to DynamoDB: {str(e)}")
            raise
    
    def process_cost_data(self, raw_data: Dict) -> List[Dict]:
        """Process raw cost data into summary format.
        
        Args:
            raw_data: Raw Cost Explorer response
            
        Returns:
            List of processed cost summaries
        """
        summaries = []
        
        for time_period in raw_data.get('ResultsByTime', []):
            date = time_period['TimePeriod']['Start']
            
            for group in time_period.get('Groups', []):
                service = group['Keys'][0] if len(group['Keys']) > 0 else 'Unknown'
                resource_id = group['Keys'][1] if len(group['Keys']) > 1 else 'N/A'
                
                amortized_cost = float(group['Metrics']['AmortizedCost']['Amount'])
                usage_quantity = float(group['Metrics']['UsageQuantity']['Amount'])
                
                summary = {
                    'date': date,
                    'service': service,
                    'resource_id': resource_id,
                    'amortized_cost': amortized_cost,
                    'usage_quantity': usage_quantity,
                    'timestamp': datetime.utcnow().isoformat()
                }
                summaries.append(summary)
        
        return summaries
    
    def collect_last_n_days(self, days: int = 90) -> List[Dict]:
        """Collect cost data for the last N days.
        
        Args:
            days: Number of days to collect
            
        Returns:
            List of cost summaries
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        raw_data = self.fetch_cost_data(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        # Store raw data
        if self.s3_bucket:
            self.store_to_s3(raw_data, end_date.isoformat())
        
        # Process and store summaries
        summaries = self.process_cost_data(raw_data)
        
        if self.dynamodb_table:
            for summary in summaries:
                self.store_to_dynamodb(summary)
        
        return summaries
