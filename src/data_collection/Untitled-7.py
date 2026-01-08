#!/usr/bin/env python3
"""
CloudWatch Cost Analysis Script
Analyzes CloudWatch usage and provides cost optimization recommendations.
"""

import logging
from datetime import datetime, timedelta
from src.data_collection.cloudwatch.collector import CloudWatchCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def analyze_cloudwatch_costs(region: str = 'us-east-1'):
    """Perform comprehensive CloudWatch cost analysis."""
    
    logger.info(f"Starting CloudWatch cost analysis for region: {region}")
    collector = CloudWatchCollector(region=region)
    
    # 1. Analyze Custom Metrics
    print("\n" + "="*80)
    print("CUSTOM METRICS ANALYSIS")
    print("="*80)
    
    custom_metrics = collector.get_custom_metric_count()
    total_custom = sum(custom_metrics.values())
    
    if total_custom > 0:
        print(f"Found {total_custom} custom metrics")
        
        # Calculate cost
        if total_custom <= 10000:
            cost = total_custom * 0.30
        else:
            cost = (10000 * 0.30) + ((total_custom - 10000) * 0.10)
        
        print(f"Estimated monthly cost: ${cost:.2f}")
        
        print("\nBreakdown by namespace:")
        for namespace, count in sorted(custom_metrics.items(), key=lambda x: x[1], reverse=True):
            print(f"  {namespace}: {count} metrics")
    else:
        print("No custom metrics found")
    
    # 2. Analyze Alarms
    print("\n" + "="*80)
    print("ALARMS ANALYSIS")
    print("="*80)
    
    alarm_stats = collector.get_alarm_count()
    
    print(f"Total alarms: {alarm_stats['total_alarms']}")
    print(f"  Standard: {alarm_stats['standard_alarms']} ($0.10/alarm)")
    print(f"  High-resolution: {alarm_stats['high_resolution_alarms']} ($0.30/alarm)")
    print(f"  Composite: {alarm_stats['composite_alarms']} ($0.50/alarm)")
    
    alarm_cost = (
        alarm_stats['standard_alarms'] * 0.10 +
        alarm_stats['high_resolution_alarms'] * 0.30 +
        alarm_stats['composite_alarms'] * 0.50
    )
    
    print(f"\nEstimated monthly alarm cost: ${alarm_cost:.2f}")
    
    # 3. Analyze Log Groups
    print("\n" + "="*80)
    print("LOG GROUPS ANALYSIS")
    print("="*80)
    
    log_groups = collector.get_log_group_metrics()
    
    if log_groups:
        total_storage_gb = sum(lg['stored_gb'] for lg in log_groups)
        storage_cost = total_storage_gb * 0.03  # $0.03/GB
        
        print(f"Total log groups: {len(log_groups)}")
        print(f"Total storage: {total_storage_gb:.2f} GB")
        print(f"Estimated monthly storage cost: ${storage_cost:.2f}")
        
        print("\nTop 5 largest log groups:")
        for i, lg in enumerate(log_groups[:5], 1):
            print(f"  {i}. {lg['name']}")
            print(f"     Size: {lg['stored_gb']:.2f} GB")
            print(f"     Retention: {lg['retention_days']}")
            
            # Recommendation
            if lg['retention_days'] == 'Never expire':
                print(f"     ⚠️  RECOMMENDATION: Set retention policy to reduce costs")
            elif isinstance(lg['retention_days'], int) and lg['retention_days'] > 30:
                print(f"     💡 Consider reducing retention to 30 days or less")
    else:
        print("No log groups found")
    
    # 4. Summary
    print("\n" + "="*80)
    print("COST SUMMARY")
    print("="*80)
    
    total_cost = alarm_cost
    
    if total_custom > 0:
        if total_custom <= 10000:
            metric_cost = total_custom * 0.30
        else:
            metric_cost = (10000 * 0.30) + ((total_custom - 10000) * 0.10)
        total_cost += metric_cost
    
    if log_groups:
        total_cost += storage_cost
    
    print(f"Estimated total monthly CloudWatch cost: ${total_cost:.2f}")
    
    # Recommendations
    print("\n" + "="*80)
    print("COST OPTIMIZATION RECOMMENDATIONS")
    print("="*80)
    
    recommendations = []
    
    if total_custom > 100:
        recommendations.append("Review custom metrics - consolidate or remove unused metrics")
    
    if alarm_stats['high_resolution_alarms'] > 10:
        recommendations.append(f"Convert {alarm_stats['high_resolution_alarms']} high-resolution alarms to standard (save ${alarm_stats['high_resolution_alarms'] * 0.20:.2f}/month)")
    
    if log_groups:
        never_expire = [lg for lg in log_groups if lg['retention_days'] == 'Never expire']
        if never_expire:
            recommendations.append(f"Set retention policies on {len(never_expire)} log groups with unlimited retention")
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
    else:
        print("No major optimization opportunities found. Great job!")
    
    logger.info("CloudWatch cost analysis completed")


if __name__ == '__main__':
    analyze_cloudwatch_costs(region='us-east-1')