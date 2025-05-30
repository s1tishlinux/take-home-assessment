# Part 2: Model Monitoring Service Implementation (1.5 hours)

## Scenario
Your company needs a model monitoring service that can detect data drift in production ML models. The service should continuously monitor incoming prediction requests and alert when the data distribution significantly differs from the training data.

## Your Tasks

### 1. Build Data Drift Detection Service (45 minutes)
Create a Python service (`drift_detector.py`) that:
- Accepts incoming prediction data via REST API
- Compares feature distributions against baseline training data
- Calculates drift metrics (KL divergence, PSI, etc.)
- Triggers alerts when drift exceeds thresholds

### 2. Containerize the Service (30 minutes)
- Create `Dockerfile` for the monitoring service
- Include proper multi-stage build
- Optimize for production use (security, size)

### 3. Kubernetes Deployment (15 minutes)
- Create `k8s-deployment.yml` with proper resource limits
- Include health checks and environment configuration
- Add service and ingress configuration

## Requirements Specification

### API Endpoints
```
POST /monitor/predict
- Accepts prediction request data
- Returns drift score and status
- Logs metrics for monitoring

GET /monitor/health
- Returns service health status
- Includes drift detection status

GET /monitor/metrics
- Returns current drift metrics
- Compatible with Prometheus scraping
```

### Data Drift Detection
- Support both numerical and categorical features
- Use Population Stability Index (PSI) for numerical features
- Use Chi-square test for categorical features
- Configurable drift thresholds
- Alert when drift score > 0.2 (warning) or > 0.5 (critical)

### Sample Data Format
```json
{
  "features": {
    "age": 35,
    "income": 50000,
    "tenure_months": 24,
    "product_category": "premium"
  },
  "model_version": "v1.2.0",
  "timestamp": "2025-05-29T10:30:00Z"
}
```

## Deliverables

1. **drift_detector.py** - Main monitoring service
2. **Dockerfile** - Container configuration
3. **k8s-deployment.yml** - Kubernetes deployment manifest
4. **requirements.txt** - Python dependencies
5. **test_drift_detector.py** - Unit tests for core functionality
6. **baseline_data.json** - Sample baseline data for testing

## Technical Specifications

### Framework Requirements
- Use Flask or FastAPI for REST API
- Include request validation with Pydantic/Marshmallow
- Add structured logging with JSON format
- Include Prometheus metrics export

### Docker Requirements
- Use Python 3.9+ base image
- Multi-stage build for smaller image size
- Non-root user for security
- Health check endpoint

### Kubernetes Requirements
- Resource limits: 500m CPU, 1Gi memory
- Liveness and readiness probes
- ConfigMap for configuration
- HorizontalPodAutoscaler for scaling

## Bonus Points (if time allows)
- Add Redis caching for baseline data
- Implement batch drift analysis endpoint
- Add data quality checks (missing values, outliers)
- Create alerting integration (webhook/Slack)

## Testing Your Implementation

```bash
# Build and run locally
docker build -t drift-detector .
docker run -p 8080:8080 drift-detector

# Test the API
curl -X POST http://localhost:8080/monitor/predict \
  -H "Content-Type: application/json" \
  -d '{"features": {"age": 35, "income": 50000}}'

# Check health
curl http://localhost:8080/monitor/health
```

---

**Time Check**: After 1.5 hours total (2.5 hours elapsed), move to Part 3. Focus on core functionality over bonus features.
