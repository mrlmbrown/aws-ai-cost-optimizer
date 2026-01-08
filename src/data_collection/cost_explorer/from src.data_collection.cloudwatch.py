from src.data_collection.cloudwatch.collector import CloudWatchCollector

# Initialize for a specific region
collector = CloudWatchCollector(profile_name='default', region='us-east-1')

# Collect metrics
metrics = collector.collect_metrics()

# Display results
for metric in metrics:
    print(f"Metric: {metric['MetricName']}, Value: {metric['Value']}")