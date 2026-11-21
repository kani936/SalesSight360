
USE salessight360;

-- 1. Weighted pipeline forecast by team and region
SELECT
    r.region,
    r.team,
    COUNT(l.lead_id) AS open_leads,

    ROUND(SUM(l.expected_deal_value), 2)
        AS total_pipeline_value,

    ROUND(SUM(
        l.expected_deal_value *
        CASE
            WHEN l.stage = 'New' THEN 0.05
            WHEN l.stage = 'Contacted' THEN 0.10
            WHEN l.stage = 'Qualified' THEN 0.25
            WHEN l.stage = 'Proposal' THEN 0.50
            WHEN l.stage = 'Negotiation' THEN 0.75
            ELSE 0
        END
    ), 2) AS weighted_forecast

FROM crm_leads l
JOIN sales_reps r
    ON l.rep_id = r.rep_id

WHERE l.stage NOT IN ('Closed Won', 'Closed Lost')

GROUP BY r.region, r.team
ORDER BY weighted_forecast DESC;

-- 2. Weighted forecast by sales stage
SELECT
    stage,
    COUNT(*) AS total_leads,

    ROUND(SUM(expected_deal_value), 2)
        AS pipeline_value,

    CASE
        WHEN stage = 'New' THEN 0.05
        WHEN stage = 'Contacted' THEN 0.10
        WHEN stage = 'Qualified' THEN 0.25
        WHEN stage = 'Proposal' THEN 0.50
        WHEN stage = 'Negotiation' THEN 0.75
        ELSE 0
    END AS stage_probability,

    ROUND(SUM(expected_deal_value) *
        CASE
            WHEN stage = 'New' THEN 0.05
            WHEN stage = 'Contacted' THEN 0.10
            WHEN stage = 'Qualified' THEN 0.25
            WHEN stage = 'Proposal' THEN 0.50
            WHEN stage = 'Negotiation' THEN 0.75
            ELSE 0
        END, 2) AS weighted_forecast

FROM crm_leads

WHERE stage NOT IN ('Closed Won', 'Closed Lost')

GROUP BY stage
ORDER BY weighted_forecast DESC;

-- 3. Monthly actual revenue versus sales targets
WITH actual_revenue AS (
    SELECT
        r.team,
        DATE_FORMAT(o.order_date, '%Y-%m-01') AS sales_month,
        SUM(o.revenue) AS actual_revenue

    FROM orders o
    JOIN sales_reps r
        ON o.rep_id = r.rep_id

    WHERE o.order_status = 'Delivered'

    GROUP BY r.team, DATE_FORMAT(o.order_date, '%Y-%m-01')
)

SELECT
    t.team,
    DATE_FORMAT(t.month, '%Y-%m') AS sales_month,

    ROUND(t.sales_target, 2) AS sales_target,

    ROUND(COALESCE(a.actual_revenue, 0), 2)
        AS actual_revenue,

    ROUND(
        COALESCE(a.actual_revenue, 0) - t.sales_target,
        2
    ) AS revenue_variance,

    ROUND(
        100.0 * COALESCE(a.actual_revenue, 0)
        / NULLIF(t.sales_target, 0),
        2
    ) AS target_achievement_pct

FROM sales_targets t

LEFT JOIN actual_revenue a
    ON a.team = t.team
    AND a.sales_month = DATE_FORMAT(t.month, '%Y-%m-01')

ORDER BY t.month, t.team;