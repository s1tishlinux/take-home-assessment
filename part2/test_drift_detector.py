#!/usr/bin/env python3
"""
Unit tests for drift detector service
"""
import json
import os
import pytest
from fastapi.testclient import TestClient

# Import the app from drift_detector.py
from drift_detector import app, calculate_psi, calculate_chi_square, detect_drift

# Create test client
client = TestClient(app)

# Sample data for testing
SAMPLE_BASELINE = {
    "features": {
        "age": {
            "type": "numerical",
            "values": [30, 40, 50, 60],
            "mean": 45.0,
            "std": 12.5
        },
        "product_category": {
            "type": "categorical",
            "distribution": {
                "basic": 0.3,
                "standard": 0.4,
                "premium": 0.2,
                "enterprise": 0.1
            }
        }
    }
}

def test_health_endpoint():
    """Test the health check endpoint"""
    response = client.get("/monitor/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"

def test_metrics_endpoint():
    """Test the metrics endpoint"""
    response = client.get("/monitor/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"

def test_predict_endpoint():
    """Test the prediction monitoring endpoint"""
    # Mock baseline data
    app.state.baseline_data = SAMPLE_BASELINE
    
    # Test request
    request_data = {
        "features": {
            "age": 35,
            "income": 50000,
            "tenure_months": 24,
            "product_category": "premium"
        },
        "model_version": "v1.2.0",
        "timestamp": "2023-05-29T10:30:00Z"
    }
    
    response = client.post("/monitor/predict", json=request_data)
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "drift_detected" in data
    assert "drift_score" in data
    assert "severity" in data
    assert "feature_scores" in data
    assert "timestamp" in data

def test_calculate_psi():
    """Test PSI calculation function"""
    # Test with identical distributions
    expected = [1, 2, 3, 4, 5]
    actual = [1, 2, 3, 4, 5]
    psi = calculate_psi(expected, actual)
    assert psi >= 0
    assert psi < 0.1  # Should be very low for identical distributions
    
    # Test with different distributions
    expected = [1, 2, 3, 4, 5]
    actual = [10, 20, 30, 40, 50]
    psi = calculate_psi(expected, actual)
    assert psi > 0.1  # Should indicate drift

def test_calculate_chi_square():
    """Test chi-square calculation function"""
    # Test with identical distributions
    expected = {"A": 10, "B": 20, "C": 30}
    actual = {"A": 10, "B": 20, "C": 30}
    chi = calculate_chi_square(expected, actual)
    assert chi >= 0
    assert chi < 0.1  # Should be very low for identical distributions
    
    # Test with different distributions
    expected = {"A": 10, "B": 20, "C": 30}
    actual = {"A": 30, "B": 10, "C": 5}
    chi = calculate_chi_square(expected, actual)
    assert chi > 0.1  # Should indicate drift

def test_detect_drift():
    """Test drift detection function"""
    # Mock baseline data
    global baseline_data
    baseline_data = SAMPLE_BASELINE
    
    # Test with normal data (no drift)
    features = {
        "age": 45,
        "product_category": "standard"
    }
    result = detect_drift(features)
    assert "drift_detected" in result
    assert "drift_score" in result
    assert "severity" in result
    
    # Test with drifting data
    features = {
        "age": 90,  # Far outside normal range
        "product_category": "enterprise"  # Least common category
    }
    result = detect_drift(features)
    assert "drift_detected" in result
    assert "drift_score" in result
    assert "severity" in result

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])