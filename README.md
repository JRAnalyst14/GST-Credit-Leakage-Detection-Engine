# GST Credit Leakage Detection Engine

An advanced data analytics system for detecting Input Tax Credit (ITC) leakage in India's GST framework using machine learning, anomaly detection, and time-series forecasting.

## Features

- **Machine Learning Vendor Risk Scoring**: Uses Random Forest to predict vendor compliance risk
- **Anomaly Detection**: Identifies unusual transactions using Isolation Forest
- **Time-Series Forecasting**: Predicts ITC trends and leakage using Prophet
- **Interactive Dashboard**: Streamlit app with Plotly visualizations
- **REST API**: FastAPI endpoints for integration
- **Advanced Reconciliation**: Configurable matching with fuzzy logic

## Tech Stack

- **Programming**: Python
- **Libraries**: NumPy, Pandas, Scikit-Learn, Plotly, Prophet, FastAPI
- **Database**: MySQL
- **Visualization**: Streamlit, Plotly
- **ML Models**: Random Forest, Isolation Forest, Prophet

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure MySQL database in `config.py`
4. Run the pipeline:
   ```bash
   python orchestrator.py
   ```

## Usage

### Data Pipeline
```bash
python orchestrator.py
```

### Dashboard
```bash
streamlit run dashboard.py
```

### API
```bash
python api.py
```

### Individual Modules
- `python vendor_risk_analysis.py` - Train and run ML risk scoring
- `python anomaly_detection.py` - Detect anomalous transactions
- `python time_series_analysis.py` - Generate forecasts

## Project Structure

- `orchestrator.py` - Main pipeline
- `data_loader.py` - Database setup and data ingestion
- `reconciliation_engine.py` - Invoice matching logic
- `vendor_risk_analysis.py` - ML-based risk scoring
- `anomaly_detection.py` - Transaction anomaly detection
- `time_series_analysis.py` - Forecasting module
- `itc_leakage_calculator.py` - Leakage calculation
- `dashboard.py` - Streamlit visualization
- `api.py` - FastAPI endpoints
- `config.py` - Configuration settings
- `schema.sql` - Database schema

## Advanced Features

1. **ML Risk Scoring**: Replaces rule-based scoring with trained Random Forest model
2. **Anomaly Detection**: Uses Isolation Forest to flag suspicious transactions
3. **Time-Series Analysis**: Forecasts ITC trends using Prophet for proactive insights
4. **Interactive Visualizations**: Plotly charts for better data exploration
5. **API Integration**: RESTful endpoints for production deployment

## Datasets

- `purchase_register.csv` - Purchase transactions
- `gstr2b_data.csv` - Supplier GST filings
- `vendor_master.csv` - Vendor information
- `vendor_filing_compliance.csv` - Filing history

## Output Files

- `models/` - Trained ML models
- `itc_forecast.csv` - ITC trend predictions
- `leakage_forecast.csv` - Leakage predictions
- PNG files for forecast plots

## Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Use type hints and docstrings