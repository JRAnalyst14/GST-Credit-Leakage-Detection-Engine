-- GST Tax Credit Leakage Detection Insights
-- This file contains 10 SQL queries that provide valuable insights into GST compliance and ITC leakage

USE gst_leakage_db;

-- Insight 1: Total ITC Claimed vs Matched by Vendor
SELECT
    vm.vendor_name,
    vm.state,
    ils.total_itc_claimed,
    ils.itc_matched,
    ils.itc_at_risk,
    ROUND((ils.itc_at_risk / NULLIF(ils.total_itc_claimed, 0)) * 100, 2) AS leakage_percentage
FROM vendor_master vm
JOIN itc_leakage_summary ils ON vm.vendor_id = ils.vendor_id
ORDER BY ils.itc_at_risk DESC
LIMIT 20;

-- Insight 2: Top Vendors by Leakage Amount
SELECT
    vm.vendor_name,
    vm.gstin,
    vm.state,
    SUM(ils.itc_at_risk) AS total_leakage,
    AVG(ils.leakage_percentage) AS avg_leakage_percentage
FROM vendor_master vm
JOIN itc_leakage_summary ils ON vm.vendor_id = ils.vendor_id
GROUP BY vm.vendor_id, vm.vendor_name, vm.gstin, vm.state
ORDER BY total_leakage DESC
LIMIT 10;

-- Insight 3: Mismatch Rate by State
SELECT
    vm.state,
    COUNT(DISTINCT vm.vendor_id) AS total_vendors,
    COUNT(DISTINCT CASE WHEN irr.match_status = 'Mismatch' THEN irr.reconciliation_id END) AS mismatch_count,
    ROUND(
        (COUNT(DISTINCT CASE WHEN irr.match_status = 'Mismatch' THEN irr.reconciliation_id END) /
         NULLIF(COUNT(DISTINCT irr.reconciliation_id), 0)) * 100, 2
    ) AS mismatch_rate_percentage
FROM vendor_master vm
LEFT JOIN purchase_register pr ON vm.vendor_id = pr.vendor_id
LEFT JOIN invoice_reconciliation_results irr ON pr.purchase_invoice_id = irr.purchase_invoice_id
GROUP BY vm.state
ORDER BY mismatch_rate_percentage DESC;

-- Insight 4: Filing Compliance Trends by Tax Period
SELECT
    vfc.tax_period,
    COUNT(*) AS total_filings,
    SUM(CASE WHEN vfc.filing_status = 'On Time' THEN 1 ELSE 0 END) AS on_time_filings,
    SUM(CASE WHEN vfc.filing_status = 'Delayed' THEN 1 ELSE 0 END) AS delayed_filings,
    AVG(vfc.delay_days) AS avg_delay_days,
    ROUND(
        (SUM(CASE WHEN vfc.filing_status = 'On Time' THEN 1 ELSE 0 END) /
         NULLIF(COUNT(*), 0)) * 100, 2
    ) AS compliance_rate_percentage
FROM vendor_filing_compliance vfc
GROUP BY vfc.tax_period
ORDER BY vfc.tax_period DESC;

-- Insight 5: High-Risk Vendors Analysis
SELECT
    vm.vendor_name,
    vm.gstin,
    vm.state,
    vrs.vendor_risk_score,
    vrs.risk_category,
    vrs.mismatch_rate,
    vrs.filing_delay_frequency,
    ils.itc_at_risk
FROM vendor_master vm
JOIN vendor_risk_scores vrs ON vm.vendor_id = vrs.vendor_id
LEFT JOIN itc_leakage_summary ils ON vm.vendor_id = ils.vendor_id
WHERE vrs.risk_category IN ('High', 'Critical')
ORDER BY vrs.vendor_risk_score DESC, ils.itc_at_risk DESC;

-- Insight 6: Tax Period Wise Leakage Analysis
SELECT
    ils.tax_period,
    SUM(ils.total_itc_claimed) AS total_itc_claimed,
    SUM(ils.itc_matched) AS total_itc_matched,
    SUM(ils.itc_at_risk) AS total_leakage,
    ROUND(
        (SUM(ils.itc_at_risk) / NULLIF(SUM(ils.total_itc_claimed), 0)) * 100, 2
    ) AS overall_leakage_percentage
FROM itc_leakage_summary ils
GROUP BY ils.tax_period
ORDER BY ils.tax_period DESC;

-- Insight 7: Average Filing Delay by Vendor Type
SELECT
    vm.business_type,
    COUNT(DISTINCT vm.vendor_id) AS vendor_count,
    AVG(vfc.delay_days) AS avg_delay_days,
    MAX(vfc.delay_days) AS max_delay_days,
    MIN(vfc.delay_days) AS min_delay_days
FROM vendor_master vm
JOIN vendor_filing_compliance vfc ON vm.vendor_id = vfc.vendor_id
GROUP BY vm.business_type
ORDER BY avg_delay_days DESC;

-- Insight 8: Reconciliation Status Distribution
SELECT
    irr.match_status,
    COUNT(*) AS count,
    ROUND((COUNT(*) / (SELECT COUNT(*) FROM invoice_reconciliation_results)) * 100, 2) AS percentage,
    SUM(ABS(irr.tax_difference)) AS total_tax_difference,
    AVG(ABS(irr.tax_difference)) AS avg_tax_difference
FROM invoice_reconciliation_results irr
GROUP BY irr.match_status
ORDER BY count DESC;

-- Insight 9: Business Type Wise Risk Assessment
SELECT
    vm.business_type,
    COUNT(DISTINCT vm.vendor_id) AS vendor_count,
    AVG(vrs.vendor_risk_score) AS avg_risk_score,
    SUM(ils.itc_at_risk) AS total_leakage,
    ROUND(
        (SUM(ils.itc_at_risk) / NULLIF(SUM(ils.total_itc_claimed), 0)) * 100, 2
    ) AS avg_leakage_percentage
FROM vendor_master vm
LEFT JOIN vendor_risk_scores vrs ON vm.vendor_id = vrs.vendor_id
LEFT JOIN itc_leakage_summary ils ON vm.vendor_id = ils.vendor_id
GROUP BY vm.business_type
ORDER BY avg_risk_score DESC;

-- Insight 10: Monthly ITC Trends and Leakage Patterns
SELECT
    DATE_FORMAT(pr.invoice_date, '%Y-%m') AS month_year,
    COUNT(DISTINCT pr.purchase_invoice_id) AS total_invoices,
    SUM(pr.total_tax) AS total_tax_claimed,
    SUM(CASE WHEN irr.match_status = 'Matched' THEN pr.total_tax ELSE 0 END) AS matched_tax,
    SUM(CASE WHEN irr.match_status != 'Matched' THEN pr.total_tax ELSE 0 END) AS unmatched_tax,
    ROUND(
        (SUM(CASE WHEN irr.match_status != 'Matched' THEN pr.total_tax ELSE 0 END) /
         NULLIF(SUM(pr.total_tax), 0)) * 100, 2
    ) AS monthly_leakage_percentage
FROM purchase_register pr
LEFT JOIN invoice_reconciliation_results irr ON pr.purchase_invoice_id = irr.purchase_invoice_id
GROUP BY DATE_FORMAT(pr.invoice_date, '%Y-%m')
ORDER BY month_year DESC
LIMIT 12;