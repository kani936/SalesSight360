
USE salessight360;

-- 1. Identify teams missing their monthly sales targets
WITH monthly_revenue AS (
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
    ROUND(COALESCE(m.actual_revenue, 0), 2) AS actual_revenue,

    ROUND(
        COALESCE(m.actual_revenue, 0) - t.sales_target,
        2
    ) AS revenue_variance,

    ROUND(
        100.0 * COALESCE(m.actual_revenue, 0)
        / NULLIF(t.sales_target, 0),
        2
    ) AS achievement_percentage,

    CASE
        WHEN COALESCE(m.actual_revenue, 0) < t.sales_target
            THEN 'TARGET MISSED'
        ELSE 'TARGET ACHIEVED'
    END AS target_status,

    CASE
        WHEN COALESCE(m.actual_revenue, 0) / NULLIF(t.sales_target, 0) < 0.80
            THEN 'HIGH PRIORITY'
        WHEN COALESCE(m.actual_revenue, 0) < t.sales_target
            THEN 'NEEDS ATTENTION'
        ELSE 'ON TRACK'
    END AS alert_level

FROM sales_targets t
LEFT JOIN monthly_revenue m
    ON m.team = t.team
    AND m.sales_month = DATE_FORMAT(t.month, '%Y-%m-01')

ORDER BY t.month DESC, achievement_percentage ASC;

-- 2. Find revenue contribution by region
SELECT
    region,
    COUNT(*) AS delivered_orders,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(AVG(revenue), 2) AS average_order_value,
    ROUND(
        100.0 * SUM(revenue) /
        NULLIF((SELECT SUM(revenue)
                FROM orders
                WHERE order_status = 'Delivered'), 0),
        2
    ) AS revenue_contribution_pct

FROM orders
WHERE order_status = 'Delivered'
GROUP BY region
ORDER BY total_revenue DESC;

-- 3. Compare sales representative performance
SELECT
    r.rep_name,
    r.team,
    r.region,
    COUNT(o.order_id) AS delivered_orders,
    ROUND(COALESCE(SUM(o.revenue), 0), 2) AS total_revenue,
    ROUND(COALESCE(AVG(o.revenue), 0), 2) AS average_order_value

FROM sales_reps r
LEFT JOIN orders o
    ON r.rep_id = o.rep_id
    AND o.order_status = 'Delivered'

GROUP BY r.rep_id, r.rep_name, r.team, r.region
ORDER BY total_revenue DESC;

-- 4. Monthly revenue trend
SELECT
    DATE_FORMAT(order_date, '%Y-%m') AS sales_month,
    COUNT(*) AS delivered_orders,
    ROUND(SUM(revenue), 2) AS monthly_revenue

FROM orders
WHERE order_status = 'Delivered'
GROUP BY DATE_FORMAT(order_date, '%Y-%m')
ORDER BY sales_month;