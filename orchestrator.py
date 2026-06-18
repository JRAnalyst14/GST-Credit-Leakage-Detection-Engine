import os
import sys
from data_loader import initialize_database, create_tables, load_data
from reconciliation_engine import perform_reconciliation
from vendor_risk_analysis import analyze_vendor_risk
from itc_leakage_calculator import calculate_itc_leakage
from anomaly_detection import detect_anomalies
from time_series_analysis import forecast_itc_trends, forecast_leakage_trends

def run_pipeline():
    print("Starting Advanced GST ITC Leakage Detection Pipeline...")
    
    # Step 1: Initialize DB and Load Data
    print("\n--- Step 1: Data Ingestion ---")
    initialize_database()
    create_tables()
    load_data()
    
    # Step 2: Perform Reconciliation
    print("\n--- Step 2: Reconciliation ---")
    perform_reconciliation()
    
    # Step 3: Analyze Vendor Risk
    print("\n--- Step 3: Vendor Risk Analysis ---")
    analyze_vendor_risk(use_ml=True)
    
    # Step 4: Calculate ITC Leakage
    print("\n--- Step 4: ITC Leakage Calculation ---")
    calculate_itc_leakage()
    
    # Step 5: Anomaly Detection
    print("\n--- Step 5: Anomaly Detection ---")
    detect_anomalies()
    
    # Step 6: Time Series Forecasting
    print("\n--- Step 6: Time Series Forecasting ---")
    forecast_itc_trends()
    forecast_leakage_trends()
    
    print("\nAdvanced pipeline execution completed successfully!")

if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        print(f"Pipeline failed: {e}")
