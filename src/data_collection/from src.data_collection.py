from src.data_collection.cost_explorer.collector import CostExplorerCollector
from src.data_collection.cloudwatch.collector import CloudWatchCollector

# Initialize collectors
ce_collector = CostExplorerCollector()
cw_collector = CloudWatchCollector()

# Get actual CloudWatch costs from Cost Explorer
cloudwatch_costs = ce_collector.get_usage_by_type(
    service_name='Amazon CloudWatch',
    start_date='2026-01-01',
    end_date='2026-01-31'
)

print("Actual CloudWatch costs by usage type:")
for usage_type, data in cloudwatch_costs.items():
    print(f"  {usage_type}: ${data['cost']:.2f}")
    print(f"    Quantity: {data['quantity']:.2f}")
    print(f"    Unit cost: ${data['unit_cost']:.4f}")

# Compare with projections from collector analysis
custom_metrics = cw_collector.get_custom_metric_count()
total_custom = sum(custom_metrics.values())

print(f"\nCustom metric count: {total_custom}")
print("This helps validate cost attribution and identify discrepancies")