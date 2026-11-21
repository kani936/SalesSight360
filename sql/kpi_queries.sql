
USE salessight360;

-- KPI 1: Total number of leads
SELECT
    COUNT(*) AS total_leads
FROM crm_leads;


-- KPI 2: Total closed-won deals
SELECT
    COUNT(*) AS total_won_deals
FROM crm_leads
WHERE stage = 'Closed Won';


-- KPI 3: Win rate
SELECT
    ROUND(
        100.0 * SUM(CASE WHEN stage = 'Closed Won' THEN 1 ELSE 0 END)
        / NULLIF(
            SUM(CASE WHEN stage IN ('Closed Won', 'Closed Lost') THEN 1 ELSE 0 END),
            0
        ),
        2
    ) AS win_rate_percentage
FROM crm_leads;


-- KPI 4: Total booked revenue
SELECT
    ROUND(SUM(revenue), 2) AS total_booked_revenue
FROM orders
WHERE order_status = 'Delivered';


-- KPI 5: Average deal size
SELECT
    ROUND(AVG(revenue), 2) AS average_deal_size
FROM orders
WHERE order_status = 'Delivered';


-- KPI 6: Total successfully collected payments
SELECT
    ROUND(SUM(amount), 2) AS total_collected_payments
FROM payments
WHERE payment_status = 'Success';
