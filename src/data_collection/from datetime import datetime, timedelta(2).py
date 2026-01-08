from datetime import datetime, timedelta

# Simulated metric collector for demonstration purposes
class MetricCollector:
    def get_metric_statistics(self, namespace, metric_name, dimensions, start_time, end_time, period):
        # Simulated data for demonstration
        return {
            'average': 35.0,  # Example average CPU utilization
            'maximum': 70.0   # Example maximum CPU utilization
        }

# Initialize the metric collector
collector = MetricCollector()

# Analyze multiple resources at once
resources = [
    ('i-001', 'EC2 Instance 1'),
    ('i-002', 'EC2 Instance 2'),
    ('i-003', 'EC2 Instance 3')
]

print("Resource Utilization Summary:")
print("-" * 80)

for instance_id, name in resources:
    metrics = collector.get_metric_statistics(
        namespace='AWS/EC2',
        metric_name='CPUUtilization',
        dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
        start_time=datetime.now() - timedelta(days=14),
        end_time=datetime.now(),
        period=86400  # Daily averages
    )
    
    print(f"{name} ({instance_id}):")
    print(f"  Average CPU: {metrics['average']:.2f}%")
    print(f"  Maximum CPU: {metrics['maximum']:.2f}%")
    
    # Rightsizing recommendation
    if metrics['average'] < 40:
        print(f"  ⚠️  RECOMMENDATION: Consider downsizing (low utilization)")
    print()