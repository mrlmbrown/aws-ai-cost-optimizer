# Main Terraform configuration for AWS AI Cost Optimizer

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    # Configure backend in terraform init:
    # terraform init -backend-config="bucket=YOUR_BUCKET" \
    #   -backend-config="key=cost-optimizer/terraform.tfstate" \
    #   -backend-config="region=us-east-1"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Repository  = "github.com/mrlmbrown/aws-ai-cost-optimizer"
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
  
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

# S3 Bucket for cost data storage
module "s3_data_bucket" {
  source = "./modules/s3"

  bucket_name          = "${var.project_name}-data-${local.account_id}"
  enable_versioning    = true
  enable_encryption    = true
  retention_days       = var.cost_data_retention_days
  lifecycle_rules      = var.s3_lifecycle_rules

  tags = local.common_tags
}

# DynamoDB Tables
module "dynamodb_tables" {
  source = "./modules/dynamodb"

  project_name = var.project_name
  environment  = var.environment

  tags = local.common_tags
}

# IAM Roles for Lambda Functions
module "iam_roles" {
  source = "./modules/iam"

  project_name         = var.project_name
  environment          = var.environment
  data_bucket_arn      = module.s3_data_bucket.bucket_arn
  recommendations_table_arn = module.dynamodb_tables.recommendations_table_arn
  metrics_table_arn    = module.dynamodb_tables.metrics_table_arn

  tags = local.common_tags
}

# Lambda Functions
module "lambda_collector" {
  source = "./modules/lambda"

  function_name    = "${var.project_name}-collector"
  description      = "Collects cost and usage data from AWS Cost Explorer"
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  source_dir       = "../src/lambdas/collector"
  memory_size      = var.lambda_memory_size
  timeout          = var.lambda_timeout
  role_arn         = module.iam_roles.collector_role_arn

  environment_variables = {
    DATA_BUCKET_NAME = module.s3_data_bucket.bucket_name
    METRICS_TABLE    = module.dynamodb_tables.metrics_table_name
    AWS_REGION       = local.region
  }

  tags = local.common_tags
}

module "lambda_recommender" {
  source = "./modules/lambda"

  function_name    = "${var.project_name}-recommender"
  description      = "Generates cost optimization recommendations"
  handler          = "handler.lambda_handler"
  runtime          = "python3.11"
  source_dir       = "../src/lambdas/recommender"
  memory_size      = var.lambda_memory_size
  timeout          = var.lambda_timeout
  role_arn         = module.iam_roles.recommender_role_arn

  environment_variables = {
    DATA_BUCKET_NAME      = module.s3_data_bucket.bucket_name
    RECOMMENDATIONS_TABLE = module.dynamodb_tables.recommendations_table_name
    SAGEMAKER_ENDPOINT    = module.sagemaker.endpoint_name
  }

  tags = local.common_tags
}

# SageMaker Endpoint
module "sagemaker" {
  source = "./modules/sagemaker"

  project_name          = var.project_name
  environment           = var.environment
  instance_type         = var.sagemaker_instance_type
  instance_count        = var.sagemaker_instance_count
  model_data_bucket     = module.s3_data_bucket.bucket_name

  tags = local.common_tags
}

# EventBridge Rules for scheduling
resource "aws_cloudwatch_event_rule" "collector_schedule" {
  name                = "${var.project_name}-collector-schedule"
  description         = "Trigger cost data collection every 6 hours"
  schedule_expression = "rate(6 hours)"

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "collector_target" {
  rule      = aws_cloudwatch_event_rule.collector_schedule.name
  target_id = "CollectorLambda"
  arn       = module.lambda_collector.function_arn
}

resource "aws_lambda_permission" "allow_eventbridge_collector" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_collector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.collector_schedule.arn
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "collector_logs" {
  name              = "/aws/lambda/${module.lambda_collector.function_name}"
  retention_in_days = 30

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "recommender_logs" {
  name              = "/aws/lambda/${module.lambda_recommender.function_name}"
  retention_in_days = 30

  tags = local.common_tags
}