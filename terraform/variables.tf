variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "cost-optimizer"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "lambda_memory_size" {
  description = "Memory allocation for Lambda functions (MB)"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Timeout for Lambda functions (seconds)"
  type        = number
  default     = 300
}

variable "sagemaker_instance_type" {
  description = "SageMaker instance type for model endpoint"
  type        = string
  default     = "ml.t2.medium"
}

variable "sagemaker_instance_count" {
  description = "Number of SageMaker instances"
  type        = number
  default     = 1
}

variable "cost_data_retention_days" {
  description = "Number of days to retain cost data in S3"
  type        = number
  default     = 90
}

variable "s3_lifecycle_rules" {
  description = "S3 lifecycle rules for data management"
  type = list(object({
    id      = string
    enabled = bool
    transitions = list(object({
      days          = number
      storage_class = string
    }))
  }))
  default = [
    {
      id      = "archive-old-data"
      enabled = true
      transitions = [
        {
          days          = 30
          storage_class = "STANDARD_IA"
        },
        {
          days          = 90
          storage_class = "GLACIER"
        }
      ]
    }
  ]
}

variable "cost_threshold_auto_approve" {
  description = "Auto-approve recommendations with savings below this threshold (USD)"
  type        = number
  default     = 100
}

variable "anomaly_sensitivity" {
  description = "Sensitivity for anomaly detection (0.0-1.0)"
  type        = number
  default     = 0.95

  validation {
    condition     = var.anomaly_sensitivity >= 0 && var.anomaly_sensitivity <= 1
    error_message = "Anomaly sensitivity must be between 0.0 and 1.0."
  }
}