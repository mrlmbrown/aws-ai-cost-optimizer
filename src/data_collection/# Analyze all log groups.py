# Analyze all log groups
log_groups = collector.get_log_group_metrics()

print("Top 10 Largest Log Groups:")
print("-" * 80)
for i, log_group in enumerate(log_groups[:10], 1):
    print(f"{i}. {log_group['name']}")
    print(f"   Size: {log_group['stored_gb']:.2f} GB")
    print(f"   Retention: {log_group['retention_days']}")
    print(f"   Created: {log_group['creation_time']}")
    print()

# Calculate storage costs
# CloudWatch Logs pricing: $0.03/GB stored per month
total_storage_gb = sum(lg['stored_gb'] for lg in log_groups)
storage_cost = total_storage_gb * 0.03

print(f"Total log storage: {total_storage_gb:.2f} GB")
print(f"Estimated monthly storage cost: ${storage_cost:.2f}")