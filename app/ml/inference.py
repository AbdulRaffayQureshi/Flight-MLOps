# This script talks to MLflow, finds the absolute latest successful training run, 
# downloads the model into memory, and generates a probability score.

import mlflow
import pandas as pd

MLFLOW_URI = "http://mlflow:5000"
EXPERIMENT_NAME = "Flight_Disruption_Prediction"

def get_latest_model():
    """Fetches the most recently trained model from MLflow."""
    mlflow.set_tracking_uri(MLFLOW_URI)
    client = mlflow.tracking.MlflowClient()
    experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
    
    if not experiment:
        return None
        
    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["start_time DESC"],
        max_results=1
    )
    
    if not runs:
        return None
        
    best_run_id = runs[0].info.run_id
    model_uri = f"runs:/{best_run_id}/model"
    
    # Load the XGBoost model back into memory
    return mlflow.xgboost.load_model(model_uri)

def predict_delay(temp: float, wind: float, precip: float, plane_count: int) -> dict:
    """Passes live metrics to the loaded model to predict disruption risk."""
    model = get_latest_model()
    if not model:
        return {"error": "No trained model found. Run training first."}
        
    # Format the data exactly how XGBoost saw it during training
    input_data = pd.DataFrame([{
        'temperature': temp,
        'wind_speed': wind,
        'precipitation': precip,
        'plane_count': plane_count
    }])
    
    # Generate prediction and probability
    prediction = model.predict(input_data)[0]
    probability = model.predict_proba(input_data)[0][1] 
    
    return {
        "prediction": int(prediction),
        "probability": float(probability),
        "risk_level": "High" if prediction == 1 else "Low"
    }


