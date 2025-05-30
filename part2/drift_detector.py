#!/usr/bin/env python3
"""
Data Drift Detection Service for ML Model Monitoring
"""
import os
import json
import logging
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('drift_detector')

# Initialize FastAPI app
app = FastAPI(
    title="Model Drift Detection Service",
    description="Service for detecting data drift in ML model inputs",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
PREDICTION_COUNTER = Counter('model_predictions_total', 'Total number of predictions', ['model_version'])
DRIFT_SCORE_GAUGE = Gauge('model_drift_score', 'Current drift score', ['model_version', 'feature'])
DRIFT_ALERT_COUNTER = Counter('model_drift_alerts_total', 'Total number of drift alerts', ['model_version', 'severity'])

# Load baseline data
BASELINE_DATA_PATH = os.environ.get('BASELINE_DATA_PATH', 'baseline_data.json')

# Drift thresholds
WARNING_THRESHOLD = float(os.environ.get('DRIFT_WARNING_THRESHOLD', '0.2'))
CRITICAL_THRESHOLD = float(os.environ.get('DRIFT_CRITICAL_THRESHOLD', '0.5'))

# Data models
class FeatureData(BaseModel):
    """Model for feature data"""
    age: Optional[int] = None
    income: Optional[float] = None
    tenure_months: Optional[int] = None
    product_category: Optional[str] = None

class PredictionRequest(BaseModel):
    """Model for prediction request data"""
    features: FeatureData
    model_version: str = Field(..., description="Model version identifier")
    timestamp: str = Field(..., description="ISO format timestamp")

class DriftResponse(BaseModel):
    """Model for drift detection response"""
    drift_detected: bool
    drift_score: float
    severity: str
    feature_scores: Dict[str, float]
    timestamp: str

# Global variables
baseline_data = {}

def load_baseline_data():
    """Load baseline data from JSON file"""
    global baseline_data
    try:
        if os.path.exists(BASELINE_DATA_PATH):
            with open(BASELINE_DATA_PATH, 'r') as f:
                baseline_data = json.load(f)
            logger.info(f"Loaded baseline data from {BASELINE_DATA_PATH}")
        else:
            logger.warning(f"Baseline data file not found at {BASELINE_DATA_PATH}")
            baseline_data = {"features": {}}
    except Exception as e:
        logger.error(f"Error loading baseline data: {str(e)}")
        baseline_data = {"features": {}}

def calculate_psi(expected_array, actual_array, bins=10) -> float:
    """
    Calculate Population Stability Index (PSI) for numerical features
    
    PSI < 0.1: No significant change
    PSI < 0.2: Moderate change
    PSI >= 0.2: Significant change
    """
    if len(actual_array) == 0:
        return 0.0
        
    # Create bins based on expected distribution
    try:
        breaks = np.histogram_bin_edges(expected_array, bins=bins)
        expected_percents = np.histogram(expected_array, bins=breaks)[0] / len(expected_array)
        actual_percents = np.histogram(actual_array, bins=breaks)[0] / len(actual_array)
        
        # Replace zeros to avoid division by zero
        expected_percents = np.where(expected_percents == 0, 0.0001, expected_percents)
        actual_percents = np.where(actual_percents == 0, 0.0001, actual_percents)
        
        # Calculate PSI
        psi_value = np.sum((actual_percents - expected_percents) * np.log(actual_percents / expected_percents))
        return float(psi_value)
    except Exception as e:
        logger.error(f"Error calculating PSI: {str(e)}")
        return 0.0

def calculate_chi_square(expected_counts, actual_counts) -> float:
    """Calculate Chi-square statistic for categorical features"""
    if not expected_counts or not actual_counts:
        return 0.0
        
    try:
        # Get all unique categories
        all_categories = set(expected_counts.keys()) | set(actual_counts.keys())
        
        # Calculate chi-square statistic
        chi_square = 0
        total_expected = sum(expected_counts.values())
        total_actual = sum(actual_counts.values())
        
        for category in all_categories:
            e_count = expected_counts.get(category, 0)
            a_count = actual_counts.get(category, 0)
            
            # Convert to proportions
            e_prop = e_count / total_expected if total_expected > 0 else 0
            a_prop = a_count / total_actual if total_actual > 0 else 0
            
            # Skip if both are zero
            if e_prop == 0 and a_prop == 0:
                continue
                
            # Use small epsilon to avoid division by zero
            e_prop = max(e_prop, 0.0001)
            
            # Add to chi-square
            chi_square += ((a_prop - e_prop) ** 2) / e_prop
            
        return float(chi_square)
    except Exception as e:
        logger.error(f"Error calculating chi-square: {str(e)}")
        return 0.0

def detect_drift(features: Dict[str, Any]) -> Dict[str, Any]:
    """Detect drift in features compared to baseline"""
    if not baseline_data or "features" not in baseline_data:
        logger.warning("No baseline data available for drift detection")
        return {
            "drift_detected": False,
            "drift_score": 0.0,
            "severity": "unknown",
            "feature_scores": {}
        }
    
    feature_scores = {}
    max_score = 0.0
    
    # Process each feature
    for feature_name, feature_value in features.items():
        if feature_name not in baseline_data["features"]:
            continue
            
        baseline_feature = baseline_data["features"][feature_name]
        
        # Handle different feature types
        if isinstance(feature_value, (int, float)):
            # Numerical feature
            if "values" in baseline_feature:
                baseline_values = baseline_feature["values"]
                score = calculate_psi([baseline_values], [feature_value])
                feature_scores[feature_name] = score
                max_score = max(max_score, score)
        elif isinstance(feature_value, str):
            # Categorical feature
            if "distribution" in baseline_feature:
                baseline_dist = baseline_feature["distribution"]
                actual_dist = {feature_value: 1}
                score = calculate_chi_square(baseline_dist, actual_dist)
                feature_scores[feature_name] = score
                max_score = max(max_score, score)
    
    # Determine severity
    severity = "none"
    if max_score >= CRITICAL_THRESHOLD:
        severity = "critical"
    elif max_score >= WARNING_THRESHOLD:
        severity = "warning"
    
    return {
        "drift_detected": max_score >= WARNING_THRESHOLD,
        "drift_score": max_score,
        "severity": severity,
        "feature_scores": feature_scores
    }

@app.on_event("startup")
async def startup_event():
    """Load baseline data on startup"""
    load_baseline_data()

@app.post("/monitor/predict", response_model=DriftResponse)
async def monitor_prediction(request: PredictionRequest):
    """Monitor prediction data for drift"""
    try:
        # Increment prediction counter
        PREDICTION_COUNTER.labels(request.model_version).inc()
        
        # Extract features
        features = request.features.dict()
        
        # Detect drift
        drift_result = detect_drift(features)
        
        # Update metrics
        for feature, score in drift_result["feature_scores"].items():
            DRIFT_SCORE_GAUGE.labels(request.model_version, feature).set(score)
        
        # Record alert if drift detected
        if drift_result["drift_detected"]:
            DRIFT_ALERT_COUNTER.labels(request.model_version, drift_result["severity"]).inc()
        
        # Prepare response
        response = {
            **drift_result,
            "timestamp": datetime.now().isoformat()
        }
        
        return response
    except Exception as e:
        logger.error(f"Error processing prediction request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitor/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if baseline data is loaded
        baseline_loaded = "features" in baseline_data
        
        return {
            "status": "healthy",
            "baseline_data_loaded": baseline_loaded,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )

@app.get("/monitor/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Add Response import for metrics endpoint
from fastapi.responses import Response

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("drift_detector:app", host="0.0.0.0", port=port, reload=False)