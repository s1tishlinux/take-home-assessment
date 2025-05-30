#!/usr/bin/env python3
"""
Fixed model deployment script with proper error handling and security improvements
"""
import pickle
import os
import sys
import logging
import requests
import pandas as pd
import psycopg2
import json
from datetime import datetime
from sklearn.metrics import accuracy_score, precision_score, recall_score

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('model_deployment')

def load_model():
    """Load the trained model from the specified path"""
    try:
        model_path = os.environ.get('MODEL_PATH', './model.pkl')
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found at {model_path}")
            
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        logger.info(f"Model loaded successfully from {model_path}")
        return model
    except (FileNotFoundError, pickle.UnpicklingError) as e:
        logger.error(f"Failed to load model: {str(e)}")
        raise

def validate_model_performance():
    """Validate model performance using test data"""
    try:
        model = load_model()
        
        # Load test data
        test_data_path = "test_data.csv"
        if not os.path.exists(test_data_path):
            raise FileNotFoundError(f"Test data not found at {test_data_path}")
            
        test_data = pd.read_csv(test_data_path)
        X_test = test_data.drop('target', axis=1)
        y_test = test_data['target']
        
        predictions = model.predict(X_test)
        probabilities = model.predict_proba(X_test)[:, 1]
        
        accuracy = accuracy_score(y_test, predictions)
        precision = precision_score(y_test, predictions)
        recall = recall_score(y_test, predictions)
        
        logger.info(f"Model Performance: Accuracy={accuracy:.3f}, Precision={precision:.3f}, Recall={recall:.3f}")
        
        return accuracy, precision, recall, probabilities
    except Exception as e:
        logger.error(f"Error validating model performance: {str(e)}")
        raise

def deploy_to_api(env='production'):
    """Deploy model to API endpoint"""
    try:
        # Validate required environment variables
        api_key = os.environ.get('API_KEY')
        if not api_key:
            raise ValueError("API_KEY environment variable is required")
            
        model_path = os.environ.get('MODEL_PATH')
        if not model_path:
            raise ValueError("MODEL_PATH environment variable is required")
        
        # Get model metadata
        accuracy, precision, recall, _ = validate_model_performance()
        
        # Check if model meets quality threshold
        config_threshold = 0.75  # Could be loaded from config
        if accuracy < config_threshold:
            logger.error(f"Model accuracy ({accuracy:.3f}) below threshold ({config_threshold})")
            return None
        
        # Prepare deployment payload
        deployment_data = {
            'model_path': model_path,
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'version': os.environ.get('GITHUB_SHA', 'unknown')[:8],
            'environment': env,
            'deployed_at': datetime.now().isoformat()
        }
        
        # Deploy to ML API
        api_url = f"http://ml-api.company.com/{env}/deploy"
        
        logger.info(f"Deploying model to {api_url}")
        response = requests.post(
            api_url,
            json=deployment_data,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"Deployment failed: {response.text}")
            return None
            
        deployment_id = response.json().get('deployment_id')
        if not deployment_id:
            logger.error("No deployment ID returned from API")
            return None
            
        logger.info(f"Successfully deployed model with ID: {deployment_id}")
        return deployment_id
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Deployment error: {str(e)}")
        return None

def update_deployment_database(deployment_id, env='production'):
    """Update deployment records in database"""
    if not deployment_id:
        logger.error("Cannot update database: No deployment ID provided")
        return False
        
    try:
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Insert deployment record
        accuracy, precision, recall, _ = validate_model_performance()
        
        insert_query = """
            INSERT INTO model_deployments 
            (deployment_id, model_version, environment, accuracy, precision, recall, deployed_at, status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cursor.execute(insert_query, (
            deployment_id,
            os.environ.get('GITHUB_SHA', 'unknown')[:8],
            env,
            accuracy,
            precision,
            recall,
            datetime.now(),
            'active'
        ))
        
        # Update model registry
        update_query = """
            UPDATE model_registry 
            SET current_deployment_id = %s, last_updated = %s 
            WHERE environment = %s
        """
        
        cursor.execute(update_query, (deployment_id, datetime.now(), env))
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Database updated successfully for deployment {deployment_id}")
        return True
    except psycopg2.Error as e:
        logger.error(f"Database error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error updating deployment database: {str(e)}")
        return False

def send_slack_notification(deployment_id, env='production'):
    """Send notification to Slack"""
    if not deployment_id:
        logger.warning("Skipping notification: No deployment ID provided")
        return
        
    try:
        webhook_url = os.environ.get('SLACK_WEBHOOK')
        if not webhook_url:
            logger.info("No Slack webhook URL provided, skipping notification")
            return
            
        accuracy, precision, recall, _ = validate_model_performance()
        
        message = {
            "text": f"🚀 Model deployed successfully!",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Model Deployment Successful*\n"
                               f"Environment: {env}\n"
                               f"Deployment ID: {deployment_id}\n"
                               f"Accuracy: {accuracy:.3f}\n"
                               f"Precision: {precision:.3f}\n"
                               f"Recall: {recall:.3f}"
                    }
                }
            ]
        }
        
        response = requests.post(webhook_url, json=message, timeout=10)
        if response.status_code == 200:
            logger.info("Slack notification sent successfully")
        else:
            logger.warning(f"Failed to send Slack notification: {response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Slack notification: {str(e)}")
    except Exception as e:
        logger.error(f"Error in Slack notification: {str(e)}")

def main():
    """Main function to orchestrate the deployment process"""
    try:
        import argparse
        parser = argparse.ArgumentParser(description="Deploy ML model to specified environment")
        parser.add_argument('--env', default='production', choices=['staging', 'production'],
                           help="Deployment environment (staging or production)")
        args = parser.parse_args()
        
        logger.info(f"Starting deployment to {args.env} environment...")
        
        # Deploy model
        deployment_id = deploy_to_api(args.env)
        if not deployment_id:
            logger.error("Deployment failed, exiting")
            sys.exit(1)
        
        # Update database
        db_success = update_deployment_database(deployment_id, args.env)
        if not db_success:
            logger.error("Database update failed")
            # Continue execution but log the error
        
        # Send notification
        send_slack_notification(deployment_id, args.env)
        
        logger.info("Deployment completed successfully!")
        return 0
    except Exception as e:
        logger.critical(f"Deployment failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())