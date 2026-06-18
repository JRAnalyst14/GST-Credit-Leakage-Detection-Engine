import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from config import DB_CONFIG

# Database Connection
def get_engine():
    user = DB_CONFIG["user"]
    password = DB_CONFIG["password"]
    host = DB_CONFIG["host"]
    database = DB_CONFIG["database"]
    return create_engine(f"mysql+mysqlconnector://{user}:{password}@{host}/{database}")

# Load Data
@st.cache_data
def load_data(table_name):
    engine = get_engine()
    return pd.read_sql(f"SELECT * FROM {table_name}", engine)

# Page Configuration
st.set_page_config(page_title="GST ITC Leakage Detection Engine", layout="wide")

# Sidebar for Filtering
st.sidebar.title("Filters")
tax_period_filter = st.sidebar.multiselect("Tax Period", ["2023-Q1", "2023-Q2", "2023-Q3", "2023-Q4", "2024-Q1", "2024-Q2"])
risk_filter = st.sidebar.multiselect("Risk Category", ["Low", "Medium", "High"])

# Header
st.title("GST ITC Leakage Detection Engine")
st.markdown("---")

# Load Datasets
try:
    itc_summary = load_data("itc_leakage_summary")
    vendor_risk = load_data("vendor_risk_scores")
    rec_results = load_data("invoice_reconciliation_results")
    
    # Apply Filters
    if tax_period_filter:
        itc_summary = itc_summary[itc_summary['tax_period'].isin(tax_period_filter)]
    if risk_filter:
        vendor_risk = vendor_risk[vendor_risk['risk_category'].isin(risk_filter)]
        itc_summary = itc_summary[itc_summary['vendor_id'].isin(vendor_risk['vendor_id'])]

    # KPI Metrics
    total_itc = itc_summary['total_itc_claimed'].sum()
    matched_itc = itc_summary['itc_matched'].sum()
    at_risk_itc = itc_summary['itc_at_risk'].sum()
    leakage_pct = (at_risk_itc / total_itc * 100) if total_itc > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total ITC Claimed", f"₹{total_itc:,.2f}")
    col2.metric("Matched ITC", f"₹{matched_itc:,.2f}")
    col3.metric("ITC At Risk", f"₹{at_risk_itc:,.2f}")
    col4.metric("Leakage %", f"{leakage_pct:.2f}%")

    st.markdown("---")

    # Layout: Two Columns for Visuals
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Match Status Breakdown")
        match_counts = rec_results['match_status'].value_counts()
        fig1 = px.pie(match_counts, values=match_counts.values, names=match_counts.index, title="Match Status Distribution")
        st.plotly_chart(fig1)

    with right_col:
        st.subheader("ITC at Risk by Aging Bucket")
        aging_summary = itc_summary.groupby('aging_bucket')['itc_at_risk'].sum().reset_index()
        fig2 = px.bar(aging_summary, x='aging_bucket', y='itc_at_risk', title="ITC at Risk by Aging")
        st.plotly_chart(fig2)

    st.markdown("---")

    # Risk Distribution
    st.subheader("Vendor Risk Score Distribution")
    fig3 = px.histogram(vendor_risk, x='vendor_risk_score', nbins=20, title="Vendor Risk Score Histogram")
    st.plotly_chart(fig3)

    # Tables
    st.markdown("---")
    tab1, tab2 = st.tabs(["Top At-Risk Vendors", "Detailed Reconciliation Results"])

    with tab1:
        st.subheader("Vendors with Highest ITC Leakage")
        top_vendors = itc_summary.groupby('vendor_id').agg({
            'total_itc_claimed': 'sum',
            'itc_at_risk': 'sum',
            'leakage_percentage': 'mean'
        }).sort_values(by='itc_at_risk', ascending=False).head(10)
        st.dataframe(top_vendors)

    with tab2:
        st.subheader("Detailed Reconciliation Results")
        st.dataframe(rec_results)

except Exception as e:
    st.error(f"Error loading data: {e}")
