
USE salessight360;

-- 1. Count how many leads reached each funnel stage
WITH funnel_stages AS (
    SELECT 1 AS stage_order, 'New' AS stage
    UNION ALL SELECT 2, 'Contacted'
    UNION ALL SELECT 3, 'Qualified'
    UNION ALL SELECT 4, 'Proposal'
    UNION ALL SELECT 5, 'Negotiation'
    UNION ALL SELECT 6, 'Closed Won'
),
stage_counts AS (
    SELECT
        fs.stage_order,
        fs.stage,
        COUNT(DISTINCT h.lead_id) AS total_leads
    FROM funnel_stages fs
    LEFT JOIN lead_stage_history h
        ON h.stage = fs.stage
    GROUP BY fs.stage_order, fs.stage
)
SELECT
    stage,
    total_leads,
    LAG(total_leads) OVER (ORDER BY stage_order) AS previous_stage_leads,
    CASE
        WHEN LAG(total_leads) OVER (ORDER BY stage_order) IS NULL THEN NULL
        WHEN LAG(total_leads) OVER (ORDER BY stage_order) = 0 THEN 0
        ELSE ROUND(
            100.0 * total_leads /
            LAG(total_leads) OVER (ORDER BY stage_order),
            2
        )
    END AS conversion_from_previous_stage_pct
FROM stage_counts
ORDER BY stage_order;


-- 2. Leads currently in each stage
SELECT
    stage,
    COUNT(*) AS total_leads
FROM crm_leads
GROUP BY stage
ORDER BY total_leads DESC;


-- 3. Funnel performance by sales channel
SELECT
    channel,
    COUNT(*) AS total_leads,
    SUM(CASE WHEN stage = 'Closed Won' THEN 1 ELSE 0 END) AS won_leads,
    SUM(CASE WHEN stage = 'Closed Lost' THEN 1 ELSE 0 END) AS lost_leads,
    ROUND(
        100.0 * SUM(CASE WHEN stage = 'Closed Won' THEN 1 ELSE 0 END)
        / NULLIF(
            SUM(CASE WHEN stage IN ('Closed Won', 'Closed Lost') THEN 1 ELSE 0 END),
            0
        ),
        2
    ) AS win_rate_pct
FROM crm_leads
GROUP BY channel
ORDER BY win_rate_pct DESC;


-- 4. Monthly lead cohorts and their outcomes
SELECT
    DATE_FORMAT(lead_date, '%Y-%m') AS lead_month,
    COUNT(*) AS total_leads,
    SUM(CASE WHEN stage = 'Closed Won' THEN 1 ELSE 0 END) AS won_leads,
    SUM(CASE WHEN stage = 'Closed Lost' THEN 1 ELSE 0 END) AS lost_leads,
    ROUND(
        100.0 * SUM(CASE WHEN stage = 'Closed Won' THEN 1 ELSE 0 END)
        / NULLIF(
            SUM(CASE WHEN stage IN ('Closed Won', 'Closed Lost') THEN 1 ELSE 0 END),
            0
        ),
        2
    ) AS decided_lead_win_rate_pct
FROM crm_leads
GROUP BY DATE_FORMAT(lead_date, '%Y-%m')
ORDER BY lead_month;
