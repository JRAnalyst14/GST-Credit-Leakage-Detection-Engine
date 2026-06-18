import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os
from config import DB_CONFIG

def get_engine():
    user = DB_CONFIG["user"]
    password = DB_CONFIG["password"]
    host = DB_CONFIG["host"]
    database = DB_CONFIG["database"]
    return create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}/{database}")

def train_anomaly_model():
    """Train Isolation Forest for detecting anomalous transactions"""
    engine = get_engine()
    
    # Load transaction data
    pr_df = pd.read_sql("SELECT * FROM purchase_register", engine)
    g2b_df = pd.read_sql("SELECT * FROM gstr2b_data", engine)
    
    # Merge for features
    merged = pd.merge(pr_df, g2b_df, on=['supplier_gstin', 'invoice_number'], how='outer', suffixes=('_pr', '_g2b'))
    merged['invoice_value_g2b'] = merged[['taxable_value_g2b', 'igst_g2b', 'cgst_g2b', 'sgst_g2b']].sum(axis=1, skipna=True).fillna(0)
    
    # Select numerical features for anomaly detection
    features = ['total_tax', 'igst_g2b', 'cgst_g2b', 'sgst_g2b', 'invoice_value_g2b']
    merged_features = merged[features].fillna(0)
    
    # Scale features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(merged_features)
    
    # Train Isolation Forest
    model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
    model.fit(scaled_features)
    
    # Save model and scaler
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/anomaly_model.pkl')
    joblib.dump(scaler, 'models/anomaly_scaler.pkl')
    
    print("Anomaly detection model trained and saved.")
    return model, scaler

def detect_anomalies():
    """Detect anomalous transactions"""
    engine = get_engine()
    
    # Load data
    pr_df = pd.read_sql("SELECT * FROM purchase_register", engine)
    g2b_df = pd.read_sql("SELECT * FROM gstr2b_data", engine)
    
    merged = pd.merge(pr_df, g2b_df, on=['supplier_gstin', 'invoice_number'], how='outer', suffixes=('_pr', '_g2b'))
    merged['invoice_value_g2b'] = merged[['taxable_value_g2b', 'igst_g2b', 'cgst_g2b', 'sgst_g2b']].sum(axis=1, skipna=True).fillna(0)
    
    features = ['total_tax', 'igst_g2b', 'cgst_g2b', 'sgst_g2b', 'invoice_value_g2b']
    merged_features = merged[features].fillna(0)
    
    if os.path.exists('models/anomaly_model.pkl') and os.path.exists('models/anomaly_scaler.pkl'):
        # Load model and scaler
        model = joblib.load('models/anomaly_model.pkl')
        scaler = joblib.load('models/anomaly_scaler.pkl')
        
        scaled_features = scaler.transform(merged_features)
        anomaly_scores = model.decision_function(scaled_features)
        predictions = model.predict(scaled_features)
        
        # -1 for anomalies, 1 for normal
        merged['anomaly_score'] = anomaly_scores
        merged['is_anomaly'] = predictions == -1
    else:
        # Fallback: simple rule-based anomaly detection
        merged['anomaly_score'] = 0
        merged['is_anomaly'] = (
            (merged['total_tax'] > merged['total_tax'].quantile(0.95)) |
            (merged['total_tax'] < merged['total_tax'].quantile(0.05))
        )
    
    # Save anomalies to database (assuming we add a table or update existing)
    # For now, print summary
    anomaly_count = merged['is_anomaly'].sum()
    print(f"Detected {anomaly_count} anomalous transactions out of {len(merged)}.")
    
    return merged

if __name__ == "__main__":
    try:
        train_anomaly_model()
        detect_anomalies()
    except Exception as e:
        print(f"Error in anomaly detection: {e}")