output "data_bucket_name" {
  description = "Name of the S3 bucket storing cost data"
  value       = module.s3_data_bucket.bucket_name
}

output "data_bucket_arn" {
  description = "ARN of the S3 bucket storing cost data"
  value       = module.s3_data_bucket.bucket_arn
}

output "recommendations_table_name" {
  description = "Name of the DynamoDB table storing recommendations"
  value       = module.dynamodb_tables.recommendations_table_name
}

output "metrics_table_name" {
  description = "Name of the DynamoDB table storing metrics"
  value       = module.dynamodb_tables.metrics_table_name
}

output "collector_function_name" {
  description = "Name of the collector Lambda function"
  value       = module.lambda_collector.function_name
}

output "collector_function_arn" {
  description = "ARN of the collector Lambda function"
  value       = module.lambda_collector.function_arn
}

output "recommender_function_name" {
  description = "Name of the recommender Lambda function"
  value       = module.lambda_recommender.function_name
}

output "sagemaker_endpoint_name" {
  description = "Name of the SageMaker endpoint"
  value       = module.sagemaker.endpoint_name
}

output "cloudwatch_dashboard_url" {
  description = "URL to the CloudWatch dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${var.project_name}-${var.environment}"
}

output "deployment_info" {
  description = "Deployment information"
  value = {
    project     = var.project_name
    environment = var.environment
    region      = var.aws_region
    account_id  = data.aws_caller_identity.current.account_id
  }
}