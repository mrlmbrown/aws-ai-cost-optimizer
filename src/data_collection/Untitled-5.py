# Identify which streams in a log group are using the most storage
log_group_name = '/aws/lambda/my-function'

top_streams = collector.get_high_volume_log_streams(
    log_group_name=log_group_name,
    limit=10
)

print(f"Top log streams in {log_group_name}:")
print("-" * 80)
for i, stream in enumerate(top_streams, 1):
    print(f"{i}. {stream['stream_name']}")
    print(f"   Size: {stream['stored_mb']:.2f} MB")
    print(f"   Last event: {stream['last_event_time']}")
    print()