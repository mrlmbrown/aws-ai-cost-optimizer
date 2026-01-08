# Count all custom metrics in your account
custom_metrics = collector.get_custom_metric_count()

print("Custom Metrics by Namespace:")
for namespace, count in custom_metrics.items():
    print(f"  {namespace}: {count} metrics")
    
total_custom = sum(custom_metrics.values())
print(f"\nTotal custom metrics: {total_custom}")

# Calculate monthly cost estimate
# First 10,000 metrics = $0.30 per metric
# Additional metrics = $0.10 per metric
if total_custom <= 10000:
    estimated_cost = total_custom * 0.30
else:
    estimated_cost = (10000 * 0.30) + ((total_custom - 10000) * 0.10)
    
print(f"Estimated monthly cost for custom metrics: ${estimated_cost:.2f}")