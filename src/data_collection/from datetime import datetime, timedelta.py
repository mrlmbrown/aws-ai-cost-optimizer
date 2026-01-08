from datetime import datetime, timedelta

# Get CPU utilization for a specific EC2 instance
instance_id = 'i-0123456789abcdef'

cpu_metrics = collector.get_metric_statistics(
    namespace='AWS/EC2',
    metric_name='CPUUtilization',
    dimensions=[
        {'Name': 'InstanceId', 'Value': instance_id}
    ],
    start_time=datetime.now() - timedelta(days=7),
    end_time=datetime.now(),
    period=3600,  # 1 hour intervals
    statistics=['Average', 'Maximum', 'Minimum']
)

print(f"Average CPU: {cpu_metrics['Average']:.2f}%")
print(f"Maximum CPU: {cpu_metrics['Maximum']:.2f}%")
print(f"Data points collected: {cpu_metrics['DatapointCount']}")