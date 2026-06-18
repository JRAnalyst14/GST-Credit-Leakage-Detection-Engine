import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from config import DB_CONFIG, DATA_FILES
import datetime

def get_engine():
    user = DB_CONFIG["user"]
    password = DB_CONFIG["password"]
    host = DB_CONFIG["host"]
    database = DB_CONFIG["database"]
    return create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}/{database}")

def perform_reconciliation():
    engine = get_engine()
    
    # Load data from database
    pr_df = pd.read_sql("SELECT * FROM purchase_register", engine)
    g2b_df = pd.read_sql("SELECT * FROM gstr2b_data", engine)
    
    # Standardize columns for matching
    pr_df['invoice_number'] = pr_df['invoice_number'].str.strip().str.upper()
    g2b_df['invoice_number'] = g2b_df['invoice_number'].str.strip().str.upper()
    
    # Merge datasets on GSTIN and Invoice Number
    merged_df = pd.merge(
        pr_df, 
        g2b_df, 
        on=['supplier_gstin', 'invoice_number'], 
        how='outer', 
        suffixes=('_pr', '_g2b'),
        indicator=True
    )
    
    results = []
    
    for idx, row in merged_df.iterrows():
        status = "Unmatched"
        mismatch_type = ""
        tax_diff = 0
        
        if row['_merge'] == 'both':
            # Check for amount mismatch
            tax_diff = abs(row['total_tax'] - (row['igst_g2b'] + row['cgst_g2b'] + row['sgst_g2b']))
            if tax_diff < 1.0: # Tolerance of 1 Rupee
                status = "Matched"
            else:
                mismatch_type = "Amount Mismatch"
            
            # Check for time-barred (Simplified: Filing after 2 years)
            if pd.notnull(row['filing_date']):
                filing_date = pd.to_datetime(row['filing_date'])
                invoice_date = pd.to_datetime(row['invoice_date_g2b'])
                if (filing_date - invoice_date).days > 365: # Example rule
                    mismatch_type = "Time-Barred"
        
        elif row['_merge'] == 'left_only':
            status = "Unmatched"
            mismatch_type = "Missing in GSTR2B"
            tax_diff = row['total_tax']
            
        elif row['_merge'] == 'right_only':
            status = "Unmatched"
            mismatch_type = "Missing in Purchase Register"
            tax_diff = row['igst_g2b'] + row['cgst_g2b'] + row['sgst_g2b']
            
        results.append({
            "purchase_invoice_id": row['purchase_invoice_id'] if pd.notnull(row['purchase_invoice_id']) else None,
            "gstr2b_id": row['gstr2b_id'] if pd.notnull(row['gstr2b_id']) else None,
            "match_status": status,
            "mismatch_type": mismatch_type,
            "tax_difference": tax_diff,
            "reconciliation_date": datetime.date.today()
        })
        
    results_df = pd.DataFrame(results)
    
    # Add unique IDs
    results_df['reconciliation_id'] = [f"REC{str(i).zfill(7)}" for i in range(len(results_df))]
    
    # Use raw connection to truncate and append to preserve schema/foreign keys
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
        cursor.execute("TRUNCATE TABLE invoice_reconciliation_results;")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conn.commit()
        cursor.close()
        conn.close()
        
        # Save to database using append
        results_df.to_sql("invoice_reconciliation_results", engine, if_exists='append', index=False)
        print(f"Reconciliation completed. Processed {len(results_df)} records.")
    except Exception as e:
        print(f"Error saving reconciliation results: {e}")
    
    return results_df

if __name__ == "__main__":
    try:
        perform_reconciliation()
    except Exception as e:
        print(f"Error during reconciliation: {e}")
