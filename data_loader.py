import pandas as pd
from sqlalchemy import create_engine
import os
from config import DB_CONFIG, DATA_FILES

def get_engine():
    user = DB_CONFIG["user"]
    password = DB_CONFIG["password"]
    host = DB_CONFIG["host"]
    database = DB_CONFIG["database"]
    return create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}/{database}")

def initialize_database():
    # First, connect to MySQL server to create database if it doesn't exist
    import mysql.connector
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"]
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        conn.commit()
        cursor.close()
        conn.close()
        print(f"Database '{DB_CONFIG['database']}' ensured.")
    except Exception as e:
        print(f"Error creating database: {e}")

def create_tables():
    # Read the schema.sql and execute it
    import mysql.connector
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )
        cursor = conn.cursor()
        with open("schema.sql", "r") as f:
            sql_script = f.read()
        
        # Split script into individual commands
        commands = sql_script.split(";")
        for command in commands:
            if command.strip():
                cursor.execute(command)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("Tables created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")

def load_data():
    engine = get_engine()
    
    # Ordered list of tables to satisfy Foreign Key constraints
    # Parent tables first (vendor_master), then child tables
    table_order = [
        "vendor_master",
        "gstr2b_data",
        "purchase_register",
        "invoice_reconciliation_results",
        "vendor_filing_compliance",
        "itc_leakage_summary",
        "vendor_risk_scores"
    ]
    
    import mysql.connector
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )
        cursor = conn.cursor()
        
        print("Disabling foreign key checks and clearing existing data...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        for table_name in table_order:
            cursor.execute(f"TRUNCATE TABLE {table_name};")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error clearing tables: {e}")
        return

    # Load data in specific order
    for table_name in table_order:
        csv_file = DATA_FILES.get(table_name)
        if csv_file and os.path.exists(csv_file):
            print(f"Loading {csv_file} into {table_name} table...")
            try:
                df = pd.read_csv(csv_file)
                
                # Basic date parsing
                for col in df.columns:
                    if 'date' in col.lower():
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                
                # Write to SQL using 'append'
                df.to_sql(table_name, engine, if_exists='append', index=False)
                print(f"Successfully loaded {len(df)} records into {table_name}.")
            except Exception as e:
                print(f"Error loading {table_name}: {e}")
                # Optional: continue to next table or break
        else:
            print(f"File {csv_file} not found. Skipping...")

if __name__ == "__main__":
    initialize_database()
    create_tables()
    load_data()
