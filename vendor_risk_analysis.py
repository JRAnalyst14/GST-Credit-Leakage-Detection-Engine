import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import joblib
import os
from config import DB_CONFIG

def get_engine():
    user = DB_CONFIG["user"]
    password = DB_CONFIG["password"]
    host = DB_CONFIG["host"]
    database = DB_CONFIG["database"]
    return create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}/{database}")

def train_risk_model():
    """Train ML model for vendor risk scoring"""
    engine = get_engine()
    
    # Load historical data for training
    vm_df = pd.read_sql("SELECT * FROM vendor_master", engine)
    rec_df = pd.read_sql("SELECT * FROM invoice_reconciliation_results", engine)
    comp_df = pd.read_sql("SELECT * FROM vendor_filing_compliance", engine)
    pr_df = pd.read_sql("SELECT vendor_id, purchase_invoice_id, total_tax FROM purchase_register", engine)
    
    # Feature engineering
    rec_with_vendor = pd.merge(rec_df, pr_df, on='purchase_invoice_id', how='left')
    
    # Mismatch features
    mismatch_features = rec_with_vendor.groupby('vendor_id').agg({
        'purchase_invoice_id': 'count',
        'match_status': lambda x: (x == 'Unmatched').sum(),
        'tax_difference': ['mean', 'sum', 'std']
    }).fillna(0)
    mismatch_features.columns = ['total_invoices', 'unmatched_count', 'avg_tax_diff', 'total_tax_diff', 'std_tax_diff']
    mismatch_features['mismatch_rate'] = mismatch_features['unmatched_count'] / mismatch_features['total_invoices'].replace(0, 1)
    
    # Filing compliance features
    filing_features = comp_df.groupby('vendor_id').agg({
        'record_id': 'count',
        'filing_status': lambda x: (x == 'Late').sum(),
        'delay_days': ['mean', 'max']
    }).fillna(0)
    filing_features.columns = ['total_filings', 'late_count', 'avg_delay', 'max_delay']
    filing_features['filing_delay_rate'] = filing_features['late_count'] / filing_features['total_filings'].replace(0, 1)
    
    # Transaction volume features
    volume_features = pr_df.groupby('vendor_id').agg({
        'total_tax': ['sum', 'mean', 'count', 'std']
    }).fillna(0)
    volume_features.columns = ['total_volume', 'avg_transaction', 'transaction_count', 'std_transaction']
    
    # GST status
    vm_df['gst_status_score'] = vm_df['gst_status'].map({
        'Active': 0, 'Cancelled': 100, 'Suspended': 80, 'Inactive': 50
    }).fillna(0)
    
    # Combine features
    features_df = vm_df[['vendor_id', 'gst_status_score']].merge(
        mismatch_features, on='vendor_id', how='left'
    ).merge(
        filing_features, on='vendor_id', how='left'
    ).merge(
        volume_features, on='vendor_id', how='left'
    ).fillna(0)
    
    # For training, create synthetic target based on rules
    features_df['synthetic_risk'] = (
        features_df['mismatch_rate'] * 40 +
        features_df['filing_delay_rate'] * 30 +
        features_df['gst_status_score'] * 0.3 +
        np.random.normal(0, 5, len(features_df))  # Add noise
    ).clip(0, 100)
    
    # Train model
    X = features_df.drop(['vendor_id', 'synthetic_risk'], axis=1)
    y = features_df['synthetic_risk']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print(f"Model MSE: {mse}")
    
    # Save model
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/vendor_risk_model.pkl')
    
    return model

def analyze_vendor_risk(use_ml=True):
    engine = get_engine()
    
    # Load necessary data
    vm_df = pd.read_sql("SELECT * FROM vendor_master", engine)
    rec_df = pd.read_sql("SELECT * FROM invoice_reconciliation_results", engine)
    comp_df = pd.read_sql("SELECT * FROM vendor_filing_compliance", engine)
    pr_df = pd.read_sql("SELECT vendor_id, purchase_invoice_id, total_tax FROM purchase_register", engine)
    
    # Feature engineering (same as training)
    rec_with_vendor = pd.merge(rec_df, pr_df, on='purchase_invoice_id', how='left')
    
    mismatch_features = rec_with_vendor.groupby('vendor_id').agg({
        'purchase_invoice_id': 'count',
        'match_status': lambda x: (x == 'Unmatched').sum(),
        'tax_difference': ['mean', 'sum', 'std']
    }).fillna(0)
    mismatch_features.columns = ['total_invoices', 'unmatched_count', 'avg_tax_diff', 'total_tax_diff', 'std_tax_diff']
    mismatch_features['mismatch_rate'] = mismatch_features['unmatched_count'] / mismatch_features['total_invoices'].replace(0, 1)
    
    filing_features = comp_df.groupby('vendor_id').agg({
        'record_id': 'count',
        'filing_status': lambda x: (x == 'Late').sum(),
        'delay_days': ['mean', 'max']
    }).fillna(0)
    filing_features.columns = ['total_filings', 'late_count', 'avg_delay', 'max_delay']
    filing_features['filing_delay_rate'] = filing_features['late_count'] / filing_features['total_filings'].replace(0, 1)
    
    volume_features = pr_df.groupby('vendor_id').agg({
        'total_tax': ['sum', 'mean', 'count', 'std']
    }).fillna(0)
    volume_features.columns = ['total_volume', 'avg_transaction', 'transaction_count', 'std_transaction']
    
    vm_df['gst_status_score'] = vm_df['gst_status'].map({
        'Active': 0, 'Cancelled': 100, 'Suspended': 80, 'Inactive': 50
    }).fillna(0)
    
    features_df = vm_df[['vendor_id', 'gst_status_score']].merge(
        mismatch_features, on='vendor_id', how='left'
    ).merge(
        filing_features, on='vendor_id', how='left'
    ).merge(
        volume_features, on='vendor_id', how='left'
    ).fillna(0)
    
    if use_ml and os.path.exists('models/vendor_risk_model.pkl'):
        # Load and use ML model
        model = joblib.load('models/vendor_risk_model.pkl')
        X = features_df.drop('vendor_id', axis=1)
        features_df['vendor_risk_score'] = model.predict(X)
    else:
        # Fallback to rule-based
        features_df['vendor_risk_score'] = (
            (features_df['mismatch_rate'] * 100 * 0.4) + 
            (features_df['filing_delay_rate'] * 100 * 0.3) + 
            (features_df['gst_status_score'] * 0.3)
        )
    
    # Risk Category
    def categorize_risk(score):
        if score < 20: return "Low"
        elif score < 40: return "Medium"
        else: return "High"
        
    features_df['risk_category'] = features_df['vendor_risk_score'].apply(categorize_risk)
    
    # Save to database
    import mysql.connector
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )
        cursor = conn.cursor()
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("TRUNCATE TABLE vendor_risk_scores;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conn.commit()
        cursor.close()
        conn.close()
        
        # Align field name with DB schema
        features_df['filing_delay_frequency'] = features_df['filing_delay_rate']
        
        # Save to database
        features_df[['vendor_id', 'mismatch_rate', 'filing_delay_frequency', 'gst_status_score', 'vendor_risk_score', 'risk_category']].to_sql(
            "vendor_risk_scores", engine, if_exists='append', index=False
        )
        print(f"Risk analysis completed for {len(features_df)} vendors using {'ML' if use_ml else 'rule-based'}.")
    except Exception as e:
        print(f"Error saving risk analysis: {e}")
    
    return features_df

if __name__ == "__main__":
    try:
        # Train model first
        train_risk_model()
        # Then analyze
        analyze_vendor_risk(use_ml=True)
    except Exception as e:
        print(f"Error during risk analysis: {e}")
