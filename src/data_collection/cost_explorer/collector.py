import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

from src.data_collection.config import (
    AWS_PROFILE, 
    AWS_REGIONS,
    COST_PULL_FREQUENCY
)

logger = logging.getLogger(__name__)


class CostExplorerCollector:
    """Collects cost and usage data from AWS Cost Explorer API."""
    
    def __init__(self, profile_name: str = AWS_PROFILE):
        """Initialize Cost Explorer client."""
        session = boto3.Session(profile_name=profile_name)
        self.client = session.client('ce', region_name='us-east-1')  # CE is global
        
    def get_daily_costs(
        self, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        granularity: str = 'DAILY'
    ) -> Dict:
        """
        Retrieve daily cost data for specified date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            granularity: DAILY, MONTHLY, or HOURLY
            
        Returns:
            Dictionary containing cost data with timestamps
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity=granularity,
                Metrics=['UnblendedCost', 'UsageQuantity'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )
            
            logger.info(f"Retrieved cost data from {start_date} to {end_date}")
            return self._parse_cost_response(response)
            
        except Exception as e:
            logger.error(f"Failed to retrieve cost data: {str(e)}")
            raise
    
    def get_service_costs(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict]:
        """
        Get cost breakdown by AWS service.
        
        Returns:
            List of dictionaries with service name and total cost
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                ]
            )
            
            return self._aggregate_service_costs(response)
            
        except Exception as e:
            logger.error(f"Failed to retrieve service costs: {str(e)}")
            raise
    
    def get_usage_by_type(
        self,
        service_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        Get detailed usage breakdown for a specific service.
        
        Args:
            service_name: AWS service name (e.g., 'Amazon CloudWatch')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary with usage types and costs
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        try:
            response = self.client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Granularity='MONTHLY',
                Metrics=['UnblendedCost', 'UsageQuantity'],
                Filter={
                    'Dimensions': {
                        'Key': 'SERVICE',
                        'Values': [service_name]
                    }
                },
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}
                ]
            )
            
            return self._parse_usage_types(response)
            
        except Exception as e:
            logger.error(f"Failed to retrieve usage types for {service_name}: {str(e)}")
            raise
    
    def get_tagged_resources_cost(
        self,
        tag_key: str,
        tag_values: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """
        Get costs grouped by tag values for cost attribution.
        
        Args:
            tag_key: Tag key to group by (e.g., 'Environment', 'Project')
            tag_values: Optional list of specific tag values to filter
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            Dictionary with tag values and associated costs
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        try:
            params = {
                'TimePeriod': {
                    'Start': start_date,
                    'End': end_date
                },
                'Granularity': 'MONTHLY',
                'Metrics': ['UnblendedCost'],
                'GroupBy': [
                    {'Type': 'TAG', 'Key': tag_key}
                ]
            }
            
            # Add filter for specific tag values if provided
            if tag_values:
                params['Filter'] = {
                    'Tags': {
                        'Key': tag_key,
                        'Values': tag_values
                    }
                }
            
            response = self.client.get_cost_and_usage(**params)
            return self._parse_tagged_costs(response, tag_key)
            
        except Exception as e:
            logger.error(f"Failed to retrieve tagged resource costs: {str(e)}")
            raise
    
    def get_forecast(
        self,
        forecast_days: int = 30,
        metric: str = 'UNBLENDED_COST'
    ) -> Dict:
        """
        Get cost forecast for future period.
        
        Args:
            forecast_days: Number of days to forecast
            metric: UNBLENDED_COST or AMORTIZED_COST
            
        Returns:
            Dictionary with forecasted costs
        """
        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=forecast_days)).strftime('%Y-%m-%d')
        
        try:
            response = self.client.get_cost_forecast(
                TimePeriod={
                    'Start': start_date,
                    'End': end_date
                },
                Metric=metric,
                Granularity='MONTHLY'
            )
            
            return {
                'forecast_amount': float(response['Total']['Amount']),
                'forecast_period': f"{start_date} to {end_date}",
                'unit': response['Total']['Unit']
            }
            
        except Exception as e:
            logger.error(f"Failed to retrieve cost forecast: {str(e)}")
            raise
    
    def _parse_cost_response(self, response: Dict) -> Dict:
        """Parse raw Cost Explorer response into structured format."""
        parsed_data = {
            'time_period': response.get('ResultsByTime', []),
            'total_cost': 0.0,
            'by_service': {}
        }
        
        for result in response.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                service_name = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                
                if service_name not in parsed_data['by_service']:
                    parsed_data['by_service'][service_name] = 0.0
                
                parsed_data['by_service'][service_name] += cost
                parsed_data['total_cost'] += cost
        
        return parsed_data
    
    def _aggregate_service_costs(self, response: Dict) -> List[Dict]:
        """Aggregate costs by service and sort by highest cost."""
        service_costs = {}
        
        for result in response.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                service_name = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                
                if service_name not in service_costs:
                    service_costs[service_name] = 0.0
                
                service_costs[service_name] += cost
        
        # Sort by cost descending
        sorted_services = sorted(
            [{'service': k, 'cost': v} for k, v in service_costs.items()],
            key=lambda x: x['cost'],
            reverse=True
        )
        
        return sorted_services
    
    def _parse_usage_types(self, response: Dict) -> Dict:
        """Parse usage type breakdown for detailed analysis."""
        usage_data = {}
        
        for result in response.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                usage_type = group['Keys'][0]
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                quantity = float(group['Metrics']['UsageQuantity']['Amount'])
                
                usage_data[usage_type] = {
                    'cost': cost,
                    'quantity': quantity,
                    'unit_cost': cost / quantity if quantity > 0 else 0
                }
        
        return usage_data
    
    def _parse_tagged_costs(self, response: Dict, tag_key: str) -> Dict:
        """Parse costs grouped by tag values."""
        tagged_costs = {
            'tag_key': tag_key,
            'by_tag_value': {},
            'untagged_cost': 0.0
        }
        
        for result in response.get('ResultsByTime', []):
            for group in result.get('Groups', []):
                tag_value = group['Keys'][0] if group['Keys'] else 'untagged'
                cost = float(group['Metrics']['UnblendedCost']['Amount'])
                
                if tag_value == 'untagged' or tag_value == '':
                    tagged_costs['untagged_cost'] += cost
                else:
                    if tag_value not in tagged_costs['by_tag_value']:
                        tagged_costs['by_tag_value'][tag_value] = 0.0
                    tagged_costs['by_tag_value'][tag_value] += cost
        
        return tagged_costs