# MLflow provides native autologging capabilities for XGBoost. By simply declaring mlflow.xgboost.autolog(),
# the system will automatically capture all hyperparameters, training-set metrics, and serialize the model
# itself into your local mlruns directory without needing manual logging for every variable.


import duckdb
import pandas as pd
import xgboost as xgb
import mlflow
import shap
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score
from imblearn.over_sampling import SMOTE


# Configuration paths matching the Docker container volumes
DB_PATH = "/workspace/data/flights.db"
MLFLOW_URI = "http://mlflow:5000"

def load_and_prepare_data():
    """"Extract joined data from DuckDB and Prepares features/target."""
    conn = duckdb.connect(DB_PATH)

    # For this architecture setup, we create a synthetic target label
    # based on high wind and traffic volume conditions.

    query = """
        SELECT 
            w.temperature,
            w.wind_speed,
            w.precipitation,
            f.plane_count,
            CASE 
                WHEN w.wind_speed > 30 OR f.plane_count > 100 THEN 1 
                ELSE 0 
            END as high_delay_probability
        FROM weather_logs w
        JOIN flight_logs f 
          ON w.airport = f.airport 
         AND DATE_TRUNC('hour', w.timestamp) = DATE_TRUNC('hour', f.timestamp)
    """

    try:
        df = conn.execute(query).df()
    except duckdb.CatalogException:
        print("Database tables not found. Ensure Phase 2 ingestion has run.")
        df = pd.DataFrame()

    conn.close()
    return df

def train_model():
    df = load_and_prepare_data()

    if len(df) < 50:
        print("Not enough data to train. Waiting for more ingestion cycles.")
        return
    
    X = df[['temperature', 'wind_speed', 'precipitation', 'plane_count']]
    y = df['high_delay_probability']

    # 1. Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # 2. Balance the dataset using SMOTE
    smote = SMOTE(random_state=42)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)

    # 3. Connect to the MLflow tracking container
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment("Flight_Disruption_Prediction")

    # ENable automatic logging for XGBoost
    mlflow.xgboost.autolog()

    with mlflow.start_run():
        print("Training XGBoost classifier...")
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            eval_metric="logloss"
        )

        model.fit(X_train_balanced, y_train_balanced)

        # 4. Evaluate the model
        preds = model.predict(X_test)
        acc = accuracy_score(y_test, preds)
        f1 = f1_score(y_test, preds)
        
        # Log custom metrics not captured by autolog
        mlflow.log_metric("test_accuracy", acc)
        mlflow.log_metric("test_f1", f1)
        
        # 5. Generate SHAP Explainability Plot
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_test)
        
        shap.summary_plot(shap_values, X_test, show=False)
        plt.savefig("shap_summary.png", bbox_inches='tight')
        
        # Log the plot as a visual artifact in MLflow
        mlflow.log_artifact("shap_summary.png")
        plt.close()

        print(f"Training complete. Accuracy: {acc:.2f}, F1: {f1:.2f}")
        print("Model and SHAP artifacts logged successfully to MLflow.")

if __name__ == "__main__":
    train_model()





