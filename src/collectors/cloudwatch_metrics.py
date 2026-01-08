"""CloudWatch metrics collection module.

Collects EC2, RDS, and Lambda utilization metrics from CloudWatch,
stores aggregated data in S3 as Parquet files for ML training.
"""

import boto3
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import io

logger = logging.getLogger(__name__)


class CloudWatchCollector:
    """Collects utilization metrics from CloudWatch."""
    
    # Metric configurations for different resource types
    METRICS_CONFIG = {
        'EC2': {
            'Namespace': 'AWS/EC2',
            'Metrics': [
                {'Name': 'CPUUtilization', 'Stat': 'Average', 'Unit': 'Percent'},
                {'Name': 'NetworkIn', 'Stat': 'Sum', 'Unit': 'Bytes'},
                {'Name': 'NetworkOut', 'Stat': 'Sum', 'Unit': 'Bytes'},
                {'Name': 'DiskReadBytes', 'Stat': 'Sum', 'Unit': 'Bytes'},
                {'Name': 'DiskWriteBytes', 'Stat': 'Sum', 'Unit': 'Bytes'},
            ],
            'DimensionName': 'InstanceId'
        },
        'RDS': {
            'Namespace': 'AWS/RDS',
            'Metrics': [
                {'Name': 'CPUUtilization', 'Stat': 'Average', 'Unit': 'Percent'},
                {'Name': 'DatabaseConnections', 'Stat': 'Average', 'Unit': 'Count'},
                {'Name': 'FreeStorageSpace', 'Stat': 'Average', 'Unit': 'Bytes'},
                {'Name': 'ReadLatency', 'Stat': 'Average', 'Unit': 'Seconds'},
                {'Name': 'WriteLatency', 'Stat': 'Average', 'Unit': 'Seconds'},
            ],
            'DimensionName': 'DBInstanceIdentifier'
        },
        'Lambda': {
            'Namespace': 'AWS/Lambda',
            'Metrics': [
                {'Name': 'Duration', 'Stat': 'Average', 'Unit': 'Milliseconds'},
                {'Name': 'Invocations', 'Stat': 'Sum', 'Unit': 'Count'},
                {'Name': 'Errors', 'Stat': 'Sum', 'Unit': 'Count'},
                {'Name': 'ConcurrentExecutions', 'Stat': 'Maximum', 'Unit': 'Count'},
            ],
            'DimensionName': 'FunctionName'
        }
    }
    
    def __init__(self, region: str = 'us-east-1', s3_bucket: Optional[str] = None):
        """Initialize CloudWatch collector.
        
        Args:
            region: AWS region
            s3_bucket: S3 bucket for metrics storage
        """
        self.cw_client = boto3.client('cloudwatch', region_name=region)
        self.s3_client = boto3.client('s3')
        self.region = region
        self.s3_bucket = s3_bucket
    
    def get_metric_statistics(self, namespace: str, metric_name: str,
                             dimensions: List[Dict], start_time: datetime,
                             end_time: datetime, period: int = 3600,
                             statistics: List[str] = None,
                             unit: Optional[str] = None) -> List[Dict]:
        """Get statistics for a CloudWatch metric.
        
        Args:
            namespace: CloudWatch namespace (e.g., AWS/EC2)
            metric_name: Metric name (e.g., CPUUtilization)
            dimensions: List of dimension dicts [{Name: ..., Value: ...}]
            start_time: Start datetime
            end_time: End datetime
            period: Period in seconds (default 1 hour)
            statistics: List of statistics (default ['Average'])
            unit: Metric unit
            
        Returns:
            List of datapoint dictionaries
        """
        if statistics is None:
            statistics = ['Average']
        
        try:
            params = {
                'Namespace': namespace,
                'MetricName': metric_name,
                'Dimensions': dimensions,
                'StartTime': start_time,
                'EndTime': end_time,
                'Period': period,
                'Statistics': statistics
            }
            
            if unit:
                params['Unit'] = unit
            
            response = self.cw_client.get_metric_statistics(**params)
            datapoints = response.get('Datapoints', [])
            
            # Sort by timestamp
            datapoints.sort(key=lambda x: x['Timestamp'])
            
            logger.info(f"Retrieved {len(datapoints)} datapoints for {metric_name}")
            return datapoints
            
        except Exception as e:
            logger.error(f"Error fetching metric {metric_name}: {str(e)}")
            raise
    
    def collect_resource_metrics(self, resource_type: str, resource_id: str,
                                days_back: int = 15) -> pd.DataFrame:
        """Collect all metrics for a specific resource.
        
        Args:
            resource_type: Type of resource (EC2, RDS, Lambda)
            resource_id: Resource identifier
            days_back: Number of days of historical data
            
        Returns:
            DataFrame with all metrics
        """
        if resource_type not in self.METRICS_CONFIG:
            raise ValueError(f"Unsupported resource type: {resource_type}")
        
        config = self.METRICS_CONFIG[resource_type]
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days_back)
        
        dimensions = [{
            'Name': config['DimensionName'],
            'Value': resource_id
        }]
        
        all_metrics_data = []
        
        for metric_config in config['Metrics']:
            try:
                datapoints = self.get_metric_statistics(
                    namespace=config['Namespace'],
                    metric_name=metric_config['Name'],
                    dimensions=dimensions,
                    start_time=start_time,
                    end_time=end_time,
                    period=3600,  # 1 hour granularity
                    statistics=[metric_config['Stat']],
                    unit=metric_config.get('Unit')
                )
                
                for dp in datapoints:
                    all_metrics_data.append({
                        'resource_type': resource_type,
                        'resource_id': resource_id,
                        'metric_name': metric_config['Name'],
                        'timestamp': dp['Timestamp'],
                        'value': dp.get(metric_config['Stat'], 0),
                        'unit': dp.get('Unit', metric_config.get('Unit')),
                        'statistic': metric_config['Stat']
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to collect {metric_config['Name']} for {resource_id}: {str(e)}")
                continue
        
        df = pd.DataFrame(all_metrics_data)
        logger.info(f"Collected {len(df)} metric datapoints for {resource_id}")
        
        return df
    
    def collect_batch_metrics(self, resources: List[Dict],
                            days_back: int = 15) -> pd.DataFrame:
        """Collect metrics for multiple resources.
        
        Args:
            resources: List of dicts with 'type' and 'id' keys
            days_back: Number of days of historical data
            
        Returns:
            Combined DataFrame with all metrics
        """
        all_data = []
        
        for resource in resources:
            try:
                df = self.collect_resource_metrics(
                    resource_type=resource['type'],
                    resource_id=resource['id'],
                    days_back=days_back
                )
                all_data.append(df)
                
            except Exception as e:
                logger.error(f"Failed to collect metrics for {resource['id']}: {str(e)}")
                continue
        
        if all_data:
            combined_df = pd.concat(all_data, ignore_index=True)
            logger.info(f"Total metrics collected: {len(combined_df)} datapoints")
            return combined_df
        else:
            logger.warning("No metrics collected")
            return pd.DataFrame()
    
    def store_metrics_to_s3(self, df: pd.DataFrame, date_str: str) -> str:
        """Store metrics DataFrame to S3 as Parquet.
        
        Args:
            df: Metrics DataFrame
            date_str: Date string for partitioning
            
        Returns:
            S3 object key
        """
        if not self.s3_bucket:
            raise ValueError("S3 bucket not configured")
        
        if df.empty:
            logger.warning("Empty DataFrame, skipping S3 upload")
            return ""
        
        key = f"raw/cloudwatch-metrics/year={date_str[:4]}/month={date_str[5:7]}/day={date_str[8:10]}/metrics.parquet"
        
        try:
            # Convert DataFrame to Parquet in memory
            parquet_buffer = io.BytesIO()
            df.to_parquet(parquet_buffer, engine='pyarrow', compression='snappy')
            parquet_buffer.seek(0)
            
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=key,
                Body=parquet_buffer.getvalue(),
                ContentType='application/octet-stream'
            )
            
            logger.info(f"Stored metrics to s3://{self.s3_bucket}/{key}")
            return key
            
        except Exception as e:
            logger.error(f"Error storing metrics to S3: {str(e)}")
            raise
    
    def calculate_statistics(self, df: pd.DataFrame) -> Dict:
        """Calculate summary statistics from metrics.
        
        Args:
            df: Metrics DataFrame
            
        Returns:
            Dictionary of statistics
        """
        if df.empty:
            return {}
        
        stats = {}
        
        for resource_id in df['resource_id'].unique():
            resource_df = df[df['resource_id'] == resource_id]
            resource_stats = {}
            
            for metric_name in resource_df['metric_name'].unique():
                metric_df = resource_df[resource_df['metric_name'] == metric_name]
                values = metric_df['value'].values
                
                resource_stats[metric_name] = {
                    'mean': float(values.mean()),
                    'median': float(pd.Series(values).median()),
                    'p95': float(pd.Series(values).quantile(0.95)),
                    'p99': float(pd.Series(values).quantile(0.99)),
                    'max': float(values.max()),
                    'min': float(values.min()),
                    'std': float(values.std())
                }
            
            stats[resource_id] = resource_stats
        
        return stats
