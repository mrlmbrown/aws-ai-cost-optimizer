# Get alarm statistics
alarm_stats = collector.get_alarm_count()

print(f"Total alarms: {alarm_stats['total_alarms']}")
print(f"Standard alarms: {alarm_stats['standard_alarms']}")
print(f"High-resolution alarms: {alarm_stats['high_resolution_alarms']}")
print(f"Composite alarms: {alarm_stats['composite_alarms']}")

# Calculate alarm costs
# Standard alarms: $0.10/month for first 10, $0.10 each after
# High-resolution: $0.30/month each
# Composite: $0.50/month each

standard_cost = alarm_stats['standard_alarms'] * 0.10
high_res_cost = alarm_stats['high_resolution_alarms'] * 0.30
composite_cost = alarm_stats['composite_alarms'] * 0.50

total_alarm_cost = standard_cost + high_res_cost + composite_cost

print(f"\nEstimated monthly alarm costs: ${total_alarm_cost:.2f}")