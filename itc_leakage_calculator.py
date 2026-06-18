import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from config import DB_CONFIG
import datetime

def get_engine():
    user = DB_CONFIG["user"]
    password = DB_CONFIG["password"]
    host = DB_CONFIG["host"]
    database = DB_CONFIG["database"]
    return create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}/{database}")

def calculate_itc_leakage():
    engine = get_engine()
    
    # Load necessary data
    pr_df = pd.read_sql("SELECT * FROM purchase_register", engine)
    rec_df = pd.read_sql("SELECT * FROM invoice_reconciliation_results", engine)
    
    # Merge reconciliation results with purchase register
    merged_df = pd.merge(pr_df, rec_df, on='purchase_invoice_id', how='left')
    
    # Calculate Aging Bucket
    today = datetime.date.today()
    merged_df['invoice_date'] = pd.to_datetime(merged_df['invoice_date'])
    merged_df['days_overdue'] = (pd.Timestamp(today) - merged_df['invoice_date']).dt.days
    
    def get_aging_bucket(days):
        if days <= 30: return "0-30"
        elif days <= 60: return "31-60"
        else: return "60+"
        
    merged_df['aging_bucket'] = merged_df['days_overdue'].apply(get_aging_bucket)
    
    # Group by Vendor and Tax Period
    summary_df = merged_df.groupby(['vendor_id', 'tax_period']).agg({
        'total_tax': 'sum',
        'match_status': [
            lambda x: (merged_df.loc[x.index, 'total_tax'][x == 'Matched']).sum(),
            lambda x: (merged_df.loc[x.index, 'total_tax'][x == 'Unmatched']).sum()
        ]
    }).reset_index()
    
    # Rename columns
    summary_df.columns = ['vendor_id', 'tax_period', 'total_itc_claimed', 'itc_matched', 'itc_at_risk']
    
    # Calculate Leakage Percentage
    summary_df['leakage_percentage'] = (summary_df['itc_at_risk'] / summary_df['total_itc_claimed'].replace(0, 1)) * 100
    
    # Add most common aging bucket per vendor/period
    aging_info = merged_df.groupby(['vendor_id', 'tax_period'])['aging_bucket'].agg(lambda x: x.mode().iloc[0] if not x.empty else "N/A").reset_index()
    summary_df = summary_df.merge(aging_info, on=['vendor_id', 'tax_period'], how='left')
    
    # Save to database using TRUNCATE + append to preserve schema
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
        cursor.execute("TRUNCATE TABLE itc_leakage_summary;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conn.commit()
        cursor.close()
        conn.close()
        
        # Save to database
        summary_df.to_sql("itc_leakage_summary", engine, if_exists='append', index=False)
        print(f"ITC Leakage calculation completed for {len(summary_df)} records.")
    except Exception as e:
        print(f"Error saving ITC leakage calculation: {e}")
    
    return summary_df

if __name__ == "__main__":
    try:
        calculate_itc_leakage()
    except Exception as e:
        print(f"Error during leakage calculation: {e}")
