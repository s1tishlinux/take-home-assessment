# ML Model Monitoring System

## Overview
This system provides a complete MLOps pipeline for deploying and monitoring machine learning models. It includes a CI/CD pipeline for model deployment and a drift detection service that monitors model inputs in production to detect data drift.

The system consists of two main components:
1. **Model Deployment Pipeline**: Automates testing, validation, and deployment of ML models
2. **Drift Detection Service**: Monitors production data for drift compared to training data

## Quick Start

### Prerequisites
- Python 3.9+
- Docker
- Kubernetes cluster (for production deployment)
- PostgreSQL database (for model registry)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/s1tishlinux/take-home-assessment.git
   cd take-home-assessment
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements_fixed.txt
   ```

4. **Set up environment variables**
   ```bash
   # For deployment script
   export API_KEY=your_api_key
   export DATABASE_URL=postgresql://user:password@localhost:5432/ml_models
   export MODEL_PATH=./model.pkl
   
   # For drift detector
   export BASELINE_DATA_PATH=./baseline_data.json
   export DRIFT_WARNING_THRESHOLD=0.2
   export DRIFT_CRITICAL_THRESHOLD=0.5
   ```

5. **Run the deployment script**
   ```bash
   python fixed_deployment.py --env staging
   ```

6. **Run the drift detection service locally**
   ```bash
   cd part2
   python drift_detector.py
   ```

## API Reference

### Drift Detection Service

#### Monitor Prediction
```
POST /monitor/predict
```

Request body:
```json
{
  "features": {
    "age": 35,
    "income": 50000,
    "tenure_months": 24,
    "product_category": "premium"
  },
  "model_version": "v1.2.0",
  "timestamp": "2023-05-29T10:30:00Z"
}
```

Response:
```json
{
  "drift_detected": false,
  "drift_score": 0.05,
  "severity": "none",
  "feature_scores": {
    "age": 0.02,
    "income": 0.05,
    "tenure_months": 0.01,
    "product_category": 0.03
  },
  "timestamp": "2023-05-29T10:30:05Z"
}
```

#### Health Check
```
GET /monitor/health
```

Response:
```json
{
  "status": "healthy",
  "baseline_data_loaded": true,
  "timestamp": "2023-05-29T10:30:00Z"
}
```

#### Metrics
```
GET /monitor/metrics
```

Response: Prometheus-compatible metrics

## Deployment

### Docker Deployment

1. **Build the Docker image**
   ```bash
   cd part2
   docker build -t drift-detector:latest .
   ```

2. **Run the container**
   ```bash
   docker run -p 8080:8080 -v $(pwd)/baseline_data.json:/app/baseline_data.json drift-detector:latest
   ```

### Kubernetes Deployment

1. **Deploy to Kubernetes**
   ```bash
   kubectl apply -f k8s-deployment.yml
   ```

2. **Check deployment status**
   ```bash
   kubectl get pods -l app=drift-detector
   kubectl get svc drift-detector
   ```

### CI/CD Pipeline

The system includes a GitHub Actions workflow that:
1. Runs tests
2. Lints code
3. Trains and validates the model
4. Deploys to staging or production based on branch
5. Runs health checks and integration tests
6. Sends notifications on failure

## Testing

### Running Unit Tests
```bash
# Test deployment script
pytest part1/test_deployment.py -v

# Test drift detector
cd part2
pytest test_drift_detector.py -v
```

### Manual Testing
```bash
# Test drift detection API
curl -X POST http://localhost:8080/monitor/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "age": 35,
      "income": 50000,
      "tenure_months": 24,
      "product_category": "premium"
    },
    "model_version": "v1.2.0",
    "timestamp": "2023-05-29T10:30:00Z"
  }'
```

## Troubleshooting

### Common Issues

#### Deployment Script Errors
- **Database connection errors**: Verify DATABASE_URL is correct and the database is accessible
- **Model loading errors**: Ensure MODEL_PATH points to a valid model file
- **API errors**: Check API_KEY is valid and the API endpoint is reachable

#### Drift Detection Service Issues
- **Service won't start**: Check port 8080 is not in use
- **No drift detection**: Verify baseline_data.json exists and is properly formatted
- **High drift scores**: Check if incoming data is significantly different from baseline

### Logs
- Deployment script logs to console and can be redirected to a file
- Drift detection service logs to console when run directly
- In Kubernetes, view logs with `kubectl logs -l app=drift-detector`