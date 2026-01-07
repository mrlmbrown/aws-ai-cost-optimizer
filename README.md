# AWS AI-Powered Infrastructure Cost Optimizer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Terraform](https://img.shields.io/badge/terraform-1.6+-purple.svg)](https://www.terraform.io/)
[![AWS](https://img.shields.io/badge/AWS-Cost_Optimizer-orange.svg)](https://aws.amazon.com/)

## 🎯 Overview

An intelligent cost optimization system that uses machine learning to analyze AWS infrastructure spending patterns, predict cost anomalies, and automatically recommend or execute resource right-sizing actions using Terraform.

### Key Features

- **ML-Powered Predictions**: SageMaker-based models trained on historical CloudWatch and Cost Explorer data
- **Automated Right-Sizing**: Terraform modules that execute optimization recommendations
- **Anomaly Detection**: Real-time alerts for unusual spending patterns
- **Cost Attribution**: Detailed tracking by service, resource, and tag
- **RESTful API**: Integration-ready endpoints for dashboards and workflows
- **Multi-Account Support**: Centralized cost management across AWS Organizations

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      AWS Cost Explorer API                       │
│                     CloudWatch Metrics API                       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Lambda: Data Collection (Python + Boto3)                       │
│  - Fetches cost/usage data every 6 hours                        │
│  - Stores in S3 + DynamoDB                                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  SageMaker: ML Training & Inference                             │
│  - Time series anomaly detection                                │
│  - Cost prediction models (7-day, 30-day)                       │
│  - Resource utilization optimization                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Lambda: Recommendation Engine                                   │
│  - Analyzes predictions vs actuals                              │
│  - Generates Terraform HCL for right-sizing                     │
│  - Stores in DynamoDB with approval workflow                    │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step Functions: Approval & Execution Workflow                  │
│  - Manual/Auto approval based on cost threshold                 │
│  - Executes Terraform via Lambda + ECS                          │
│  - Rollback capability if issues detected                       │
└─────────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  API Gateway: REST API for External Integration                 │
│  - GET /recommendations                                          │
│  - POST /approve/{recommendation_id}                            │
│  - GET /savings/summary                                          │
└─────────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

- AWS Account with billing access
- Python 3.9+
- Terraform 1.6+
- AWS CLI configured
- IAM permissions for:
  - Cost Explorer
  - CloudWatch
  - SageMaker
  - Lambda
  - DynamoDB
  - S3
  - Step Functions
  - API Gateway

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/mrlmbrown/aws-ai-cost-optimizer.git
cd aws-ai-cost-optimizer
```

### 2. Install Python Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure AWS Credentials

```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region
```

### 4. Deploy Infrastructure with Terraform

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### 5. Train Initial ML Model

```bash
cd ../src/ml
python train_model.py --historical-days 90
```

### 6. Test the System

```bash
# Trigger data collection
aws lambda invoke --function-name cost-optimizer-collector output.json

# Check recommendations
aws dynamodb scan --table-name cost-optimizer-recommendations
```

## 📁 Project Structure

```
aws-ai-cost-optimizer/
├── README.md
├── requirements.txt
├── .gitignore
├── terraform/
│   ├── main.tf                    # Main infrastructure
│   ├── variables.tf               # Input variables
│   ├── outputs.tf                 # Output values
│   ├── modules/
│   │   ├── lambda/                # Lambda function resources
│   │   ├── sagemaker/             # SageMaker endpoint
│   │   ├── dynamodb/              # DynamoDB tables
│   │   ├── s3/                    # S3 buckets
│   │   ├── step_functions/        # Step Functions workflow
│   │   └── api_gateway/           # API Gateway
│   └── environments/
│       ├── dev.tfvars
│       └── prod.tfvars
├── src/
│   ├── lambdas/
│   │   ├── collector/             # Data collection Lambda
│   │   │   ├── handler.py
│   │   │   └── requirements.txt
│   │   ├── recommender/           # Recommendation engine
│   │   │   ├── handler.py
│   │   │   └── requirements.txt
│   │   └── executor/              # Terraform executor
│   │       ├── handler.py
│   │       └── requirements.txt
│   ├── ml/
│   │   ├── train_model.py         # Model training script
│   │   ├── predict.py             # Inference script
│   │   ├── preprocessing.py       # Data preprocessing
│   │   └── models/
│   │       ├── anomaly_detector.py
│   │       └── cost_predictor.py
│   └── utils/
│       ├── aws_clients.py         # AWS SDK helpers
│       ├── cost_analyzer.py       # Cost analysis utilities
│       └── terraform_generator.py # HCL generation
├── notebooks/
│   └── exploratory_analysis.ipynb # Jupyter notebook for EDA
├── tests/
│   ├── unit/
│   └── integration/
└── docs/
    ├── ARCHITECTURE.md
    ├── API.md
    └── DEPLOYMENT.md
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file:

```bash
AWS_REGION=us-east-1
COST_THRESHOLD_AUTO_APPROVE=100  # Auto-approve savings under $100
ANOMALY_SENSITIVITY=0.95         # 95th percentile for anomaly detection
TRAINING_LOOKBACK_DAYS=90
PREDICTION_HORIZON_DAYS=30
SAGEMAKER_INSTANCE_TYPE=ml.m5.large
```

### Terraform Variables

Edit `terraform/environments/dev.tfvars`:

```hcl
project_name = "cost-optimizer"
environment  = "dev"
aws_region   = "us-east-1"

lambda_memory_size = 512
lambda_timeout     = 300

sagemaker_instance_type = "ml.m5.large"
sagemaker_instance_count = 1

cost_data_retention_days = 90
```

## 💡 Usage Examples

### Get Cost Recommendations via API

```bash
curl -X GET https://your-api-gateway-url/recommendations \
  -H "x-api-key: YOUR_API_KEY"
```

### Approve a Recommendation

```python
import boto3

client = boto3.client('stepfunctions')
response = client.start_execution(
    stateMachineArn='arn:aws:states:region:account:stateMachine:cost-optimizer',
    input='{"recommendation_id": "rec-12345", "action": "approve"}'
)
```

### Query Savings Summary

```python
import boto3
from datetime import datetime, timedelta

ce_client = boto3.client('ce')
response = ce_client.get_cost_and_usage(
    TimePeriod={
        'Start': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
        'End': datetime.now().strftime('%Y-%m-%d')
    },
    Granularity='DAILY',
    Metrics=['UnblendedCost'],
    GroupBy=[{'Type': 'TAG', 'Key': 'CostOptimizer'}]
)
```

## 🧪 Testing

```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Test Terraform configuration
cd terraform
terraform validate
terraform fmt -check
tfsec .
```

## 📊 Metrics & Monitoring

The system tracks:

- **Cost Savings**: Total monthly savings achieved
- **Prediction Accuracy**: MAPE (Mean Absolute Percentage Error)
- **Anomaly Detection Rate**: True positives vs false positives
- **Recommendation Acceptance**: % of recommendations approved/executed
- **Execution Success Rate**: % of Terraform applies that succeed

CloudWatch dashboards are automatically created during deployment.

## 🔐 Security & IAM

### Least Privilege Policies

Each Lambda function has minimal permissions:

- **Collector**: Read-only access to Cost Explorer, CloudWatch, write to S3/DynamoDB
- **Recommender**: Read from S3/DynamoDB, invoke SageMaker, write recommendations
- **Executor**: Read recommendations, execute Terraform (limited to approved resource types)

### Encryption

- S3 buckets: AES-256 server-side encryption
- DynamoDB tables: Encrypted at rest with KMS
- Secrets: Stored in AWS Secrets Manager

## 🛣️ Roadmap

- [ ] Phase 1: Data collection and storage ✅
- [ ] Phase 2: ML model training and deployment
- [ ] Phase 3: Recommendation engine
- [ ] Phase 4: Automated execution workflow
- [ ] Phase 5: API and dashboard integration
- [ ] Phase 6: Multi-account support
- [ ] Future: Support for Azure, GCP cost optimization

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## 📝 License

MIT License - see [LICENSE](LICENSE)

## 📧 Contact

**Lennis Brown**
- GitHub: [@mrlmbrown](https://github.com/mrlmbrown)
- Portfolio: [https://mrlmbrown.github.io](https://mrlmbrown.github.io)

## 🙏 Acknowledgments

- AWS Cost Explorer API documentation
- SageMaker time series examples
- Terraform AWS provider community

---

**Note**: This is a learning project demonstrating cloud architecture, ML engineering, and infrastructure automation skills. Always test in a non-production environment first.