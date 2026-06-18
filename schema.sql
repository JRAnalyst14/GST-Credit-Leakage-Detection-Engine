CREATE DATABASE IF NOT EXISTS gst_leakage_db;
USE gst_leakage_db;

CREATE TABLE IF NOT EXISTS vendor_master (
    vendor_id VARCHAR(50) PRIMARY KEY,
    vendor_name VARCHAR(255),
    gstin VARCHAR(15),
    state VARCHAR(100),
    business_type VARCHAR(100),
    gst_status VARCHAR(50),
    registration_date DATE,
    compliance_rating DECIMAL(5, 2)
);

CREATE TABLE IF NOT EXISTS gstr2b_data (
    gstr2b_id VARCHAR(50) PRIMARY KEY,
    supplier_gstin VARCHAR(15),
    invoice_number VARCHAR(100),
    invoice_date DATE,
    tax_period VARCHAR(20),
    taxable_value DECIMAL(15, 2),
    igst DECIMAL(15, 2),
    cgst DECIMAL(15, 2),
    sgst DECIMAL(15, 2),
    filing_date DATE,
    amendment_flag TINYINT
);

CREATE TABLE IF NOT EXISTS purchase_register (
    purchase_invoice_id VARCHAR(50) PRIMARY KEY,
    vendor_id VARCHAR(50),
    supplier_gstin VARCHAR(15),
    invoice_number VARCHAR(100),
    invoice_date DATE,
    tax_period VARCHAR(20),
    taxable_value DECIMAL(15, 2),
    igst DECIMAL(15, 2),
    cgst DECIMAL(15, 2),
    sgst DECIMAL(15, 2),
    total_tax DECIMAL(15, 2),
    payment_date DATE,
    business_unit VARCHAR(100),
    FOREIGN KEY (vendor_id) REFERENCES vendor_master(vendor_id)
);

CREATE TABLE IF NOT EXISTS invoice_reconciliation_results (
    reconciliation_id VARCHAR(50) PRIMARY KEY,
    purchase_invoice_id VARCHAR(50),
    gstr2b_id VARCHAR(50),
    match_status VARCHAR(50),
    mismatch_type VARCHAR(100),
    tax_difference DECIMAL(15, 2),
    tolerance_applied TINYINT,
    reconciliation_date DATE,
    FOREIGN KEY (purchase_invoice_id) REFERENCES purchase_register(purchase_invoice_id)
);

CREATE TABLE IF NOT EXISTS vendor_filing_compliance (
    record_id VARCHAR(50) PRIMARY KEY,
    vendor_id VARCHAR(50),
    gstin VARCHAR(15),
    tax_period VARCHAR(20),
    return_type VARCHAR(50),
    filing_date DATE,
    delay_days INT,
    filing_status VARCHAR(50),
    FOREIGN KEY (vendor_id) REFERENCES vendor_master(vendor_id)
);

-- Table for ITC Leakage Summary
CREATE TABLE IF NOT EXISTS itc_leakage_summary (
    vendor_id VARCHAR(50),
    tax_period VARCHAR(20),
    total_itc_claimed DECIMAL(15, 2),
    itc_matched DECIMAL(15, 2),
    itc_at_risk DECIMAL(15, 2),
    leakage_percentage DECIMAL(10, 2),
    aging_bucket VARCHAR(50),
    PRIMARY KEY (vendor_id, tax_period),
    FOREIGN KEY (vendor_id) REFERENCES vendor_master(vendor_id)
);

CREATE TABLE IF NOT EXISTS vendor_risk_scores (
    vendor_id VARCHAR(50) PRIMARY KEY,
    mismatch_rate DECIMAL(5, 3),
    filing_delay_frequency DECIMAL(5, 3),
    gst_status_score INT,
    vendor_risk_score DECIMAL(5, 2),
    risk_category VARCHAR(20),
    FOREIGN KEY (vendor_id) REFERENCES vendor_master(vendor_id)
);
