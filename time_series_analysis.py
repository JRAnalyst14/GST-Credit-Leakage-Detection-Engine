import pandas as pd
import numpy as np
import re
from sqlalchemy import create_engine
from prophet import Prophet
import matplotlib.pyplot as plt
import os
from config import DB_CONFIG

def get_engine():
    user = DB_CONFIG["user"]
    password = DB_CONFIG["password"]
    host = DB_CONFIG["host"]
    database = DB_CONFIG["database"]
    return create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}/{database}")


def parse_tax_period(period):
    value = str(period).strip()
    if re.match(r'^\d{4}-Q[1-4]$', value):
        return pd.Period(value.replace('-', ''), freq='Q').to_timestamp()
    if re.match(r'^\d{4}Q[1-4]$', value):
        return pd.Period(value, freq='Q').to_timestamp()
    if re.match(r'^\d{4}-\d{2}$', value):
        return pd.to_datetime(value, format='%Y-%m', errors='coerce')
    if re.match(r'^\d{6}$', value):
        return pd.to_datetime(value, format='%Y%m', errors='coerce')
    return pd.to_datetime(value, errors='coerce')


def tax_period_to_timestamp(series):
    return series.astype(str).map(parse_tax_period)


def infer_tax_period_freq(series):
    values = series.astype(str).str.strip()
    if values.str.match(r'^\d{4}-Q[1-4]$').any() or values.str.match(r'^\d{4}Q[1-4]$').any():
        return 'Q'
    if values.str.match(r'^\d{4}-\d{2}$').any() or values.str.match(r'^\d{6}$').any():
        return 'MS'
    return 'D'


def forecast_itc_trends():
    """Forecast ITC trends using Prophet"""
    engine = get_engine()
    
    # Load historical ITC data
    itc_df = pd.read_sql("SELECT tax_period, SUM(total_itc_claimed) as total_itc FROM itc_leakage_summary GROUP BY tax_period ORDER BY tax_period", engine)
    
    if itc_df.empty:
        print("No historical ITC data available for forecasting.")
        return
    
    # Prepare data for Prophet
    itc_df['tax_period'] = tax_period_to_timestamp(itc_df['tax_period'])
    prophet_df = itc_df.rename(columns={'tax_period': 'ds', 'total_itc': 'y'})
    
    # Train Prophet model
    model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
    model.fit(prophet_df)
    
    # Make future predictions with matching frequency
    freq = infer_tax_period_freq(itc_df['tax_period'])
    future = model.make_future_dataframe(periods=4, freq=freq)
    forecast = model.predict(future)
    
    # Plot forecast
    fig = model.plot(forecast)
    plt.title('ITC Trend Forecast')
    plt.savefig('forecast_itc_trends.png')
    plt.close()
    
    # Save forecast to CSV
    forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_csv('itc_forecast.csv', index=False)
    
    print("ITC trend forecast completed. Check 'itc_forecast.csv' and 'forecast_itc_trends.png'.")
    
    return forecast

def forecast_leakage_trends():
    """Forecast ITC leakage trends"""
    engine = get_engine()
    
    leakage_df = pd.read_sql("SELECT tax_period, SUM(itc_at_risk) as leakage FROM itc_leakage_summary GROUP BY tax_period ORDER BY tax_period", engine)
    
    if leakage_df.empty:
        print("No historical leakage data available for forecasting.")
        return
    
    leakage_df['tax_period'] = tax_period_to_timestamp(leakage_df['tax_period'])
    prophet_df = leakage_df.rename(columns={'tax_period': 'ds', 'leakage': 'y'})
    
    model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
    model.fit(prophet_df)
    
    freq = infer_tax_period_freq(leakage_df['tax_period'])
    future = model.make_future_dataframe(periods=4, freq=freq)
    forecast = model.predict(future)
    
    fig = model.plot(forecast)
    plt.title('ITC Leakage Forecast')
    plt.savefig('forecast_leakage_trends.png')
    plt.close()
    
    forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_csv('leakage_forecast.csv', index=False)
    
    print("ITC leakage forecast completed. Check 'leakage_forecast.csv' and 'forecast_leakage_trends.png'.")
    
    return forecast

if __name__ == "__main__":
    try:
        forecast_itc_trends()
        forecast_leakage_trends()
    except Exception as e:
        print(f"Error in time series analysis: {e}")