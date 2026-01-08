"""Resource inventory collection module.

Scans AWS accounts to discover EC2, RDS, and Lambda resources,
collecting specifications, tags, and configuration details.
"""

import boto3
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ResourceInventoryCollector:
    """Collects inventory of AWS resources for cost optimization."""
    
    def __init__(self, region: str = 'us-east-1', s3_bucket: Optional[str] = None):
        """Initialize resource inventory collector.
        
        Args:
            region: AWS region
            s3_bucket: S3 bucket for inventory storage
        """
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.rds_client = boto3.client('rds', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.s3_client = boto3.client('s3')
        self.region = region
        self.s3_bucket = s3_bucket
    
    def scan_ec2_instances(self) -> List[Dict]:
        """Scan all EC2 instances in the region.
        
        Returns:
            List of EC2 instance details
        """
        instances = []
        
        try:
            paginator = self.ec2_client.get_paginator('describe_instances')
            
            for page in paginator.paginate():
                for reservation in page['Reservations']:
                    for instance in reservation['Instances']:
                        instance_data = {
                            'resource_type': 'EC2',
                            'resource_id': instance['InstanceId'],
                            'instance_type': instance['InstanceType'],
                            'state': instance['State']['Name'],
                            'launch_time': instance['LaunchTime'].isoformat(),
                            'availability_zone': instance['Placement']['AvailabilityZone'],
                            'platform': instance.get('Platform', 'Linux/UNIX'),
                            'architecture': instance.get('Architecture', 'x86_64'),
                            'vcpus': self._get_instance_vcpus(instance['InstanceType']),
                            'memory_gb': self._get_instance_memory(instance['InstanceType']),
                            'tags': self._extract_tags(instance.get('Tags', [])),
                            'private_ip': instance.get('PrivateIpAddress'),
                            'public_ip': instance.get('PublicIpAddress'),
                            'vpc_id': instance.get('VpcId'),
                            'subnet_id': instance.get('SubnetId'),
                            'monitoring': instance.get('Monitoring', {}).get('State'),
                            'scan_timestamp': datetime.utcnow().isoformat()
                        }
                        instances.append(instance_data)
            
            logger.info(f"Scanned {len(instances)} EC2 instances")
            return instances
            
        except Exception as e:
            logger.error(f"Error scanning EC2 instances: {str(e)}")
            raise
    
    def scan_rds_instances(self) -> List[Dict]:
        """Scan all RDS instances in the region.
        
        Returns:
            List of RDS instance details
        """
        instances = []
        
        try:
            paginator = self.rds_client.get_paginator('describe_db_instances')
            
            for page in paginator.paginate():
                for db_instance in page['DBInstances']:
                    instance_data = {
                        'resource_type': 'RDS',
                        'resource_id': db_instance['DBInstanceIdentifier'],
                        'instance_class': db_instance['DBInstanceClass'],
                        'engine': db_instance['Engine'],
                        'engine_version': db_instance['EngineVersion'],
                        'state': db_instance['DBInstanceStatus'],
                        'allocated_storage_gb': db_instance['AllocatedStorage'],
                        'storage_type': db_instance.get('StorageType'),
                        'multi_az': db_instance.get('MultiAZ', False),
                        'availability_zone': db_instance.get('AvailabilityZone'),
                        'vcpus': self._get_rds_vcpus(db_instance['DBInstanceClass']),
                        'memory_gb': self._get_rds_memory(db_instance['DBInstanceClass']),
                        'backup_retention_days': db_instance.get('BackupRetentionPeriod'),
                        'tags': [],  # RDS tags need separate API call
                        'scan_timestamp': datetime.utcnow().isoformat()
                    }
                    instances.append(instance_data)
            
            logger.info(f"Scanned {len(instances)} RDS instances")
            return instances
            
        except Exception as e:
            logger.error(f"Error scanning RDS instances: {str(e)}")
            raise
    
    def scan_lambda_functions(self) -> List[Dict]:
        """Scan all Lambda functions in the region.
        
        Returns:
            List of Lambda function details
        """
        functions = []
        
        try:
            paginator = self.lambda_client.get_paginator('list_functions')
            
            for page in paginator.paginate():
                for function in page['Functions']:
                    function_data = {
                        'resource_type': 'Lambda',
                        'resource_id': function['FunctionName'],
                        'runtime': function['Runtime'],
                        'memory_mb': function['MemorySize'],
                        'timeout_seconds': function['Timeout'],
                        'code_size_bytes': function['CodeSize'],
                        'last_modified': function['LastModified'],
                        'architecture': function.get('Architectures', ['x86_64'])[0],
                        'ephemeral_storage_mb': function.get('EphemeralStorage', {}).get('Size', 512),
                        'tags': [],  # Lambda tags need separate API call
                        'scan_timestamp': datetime.utcnow().isoformat()
                    }
                    functions.append(function_data)
            
            logger.info(f"Scanned {len(functions)} Lambda functions")
            return functions
            
        except Exception as e:
            logger.error(f"Error scanning Lambda functions: {str(e)}")
            raise
    
    def collect_full_inventory(self) -> Dict[str, List[Dict]]:
        """Collect complete inventory of all supported resources.
        
        Returns:
            Dictionary with resource types as keys and lists of resources
        """
        inventory = {
            'ec2_instances': self.scan_ec2_instances(),
            'rds_instances': self.scan_rds_instances(),
            'lambda_functions': self.scan_lambda_functions()
        }
        
        total_resources = sum(len(v) for v in inventory.values())
        logger.info(f"Total resources scanned: {total_resources}")
        
        return inventory
    
    def store_inventory_to_s3(self, inventory: Dict, date_str: str) -> str:
        """Store inventory data to S3.
        
        Args:
            inventory: Complete inventory dictionary
            date_str: Date string for partitioning
            
        Returns:
            S3 object key
        """
        if not self.s3_bucket:
            raise ValueError("S3 bucket not configured")
        
        key = f"raw/inventory/year={date_str[:4]}/month={date_str[5:7]}/day={date_str[8:10]}/inventory.json"
        
        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=key,
                Body=json.dumps(inventory, default=str, indent=2),
                ContentType='application/json'
            )
            
            logger.info(f"Stored inventory to s3://{self.s3_bucket}/{key}")
            return key
            
        except Exception as e:
            logger.error(f"Error storing inventory to S3: {str(e)}")
            raise
    
    @staticmethod
    def _extract_tags(tags_list: List[Dict]) -> Dict:
        """Convert AWS tags list to dictionary."""
        return {tag['Key']: tag['Value'] for tag in tags_list}
    
    @staticmethod
    def _get_instance_vcpus(instance_type: str) -> Optional[int]:
        """Get vCPU count for instance type (simplified lookup)."""
        # This is a simplified version - production should use AWS Pricing API
        vcpu_map = {
            't2.micro': 1, 't2.small': 1, 't2.medium': 2, 't2.large': 2,
            't3.micro': 2, 't3.small': 2, 't3.medium': 2, 't3.large': 2,
            'm5.large': 2, 'm5.xlarge': 4, 'm5.2xlarge': 8,
            'c5.large': 2, 'c5.xlarge': 4, 'c5.2xlarge': 8,
        }
        return vcpu_map.get(instance_type)
    
    @staticmethod
    def _get_instance_memory(instance_type: str) -> Optional[float]:
        """Get memory in GB for instance type (simplified lookup)."""
        memory_map = {
            't2.micro': 1, 't2.small': 2, 't2.medium': 4, 't2.large': 8,
            't3.micro': 1, 't3.small': 2, 't3.medium': 4, 't3.large': 8,
            'm5.large': 8, 'm5.xlarge': 16, 'm5.2xlarge': 32,
            'c5.large': 4, 'c5.xlarge': 8, 'c5.2xlarge': 16,
        }
        return memory_map.get(instance_type)
    
    @staticmethod
    def _get_rds_vcpus(instance_class: str) -> Optional[int]:
        """Get vCPU count for RDS instance class."""
        vcpu_map = {
            'db.t3.micro': 2, 'db.t3.small': 2, 'db.t3.medium': 2,
            'db.m5.large': 2, 'db.m5.xlarge': 4, 'db.m5.2xlarge': 8,
        }
        return vcpu_map.get(instance_class)
    
    @staticmethod
    def _get_rds_memory(instance_class: str) -> Optional[float]:
        """Get memory in GB for RDS instance class."""
        memory_map = {
            'db.t3.micro': 1, 'db.t3.small': 2, 'db.t3.medium': 4,
            'db.m5.large': 8, 'db.m5.xlarge': 16, 'db.m5.2xlarge': 32,
        }
        return memory_map.get(instance_class)
