

import sqlite3
import pandas as pd

DB_PATH = "ecommerce.db"

REVENUE_EXPR = "oi.quantity * oi.unit_price * (1 - oi.discount_percent/100.0)"

QUERIES = {}



QUERIES["1_revenue_per_category"] = f"""
SELECT
    p.category,
    ROUND(SUM({REVENUE_EXPR}), 2) AS total_revenue
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;
"""

QUERIES["2_top10_customers"] = f"""
SELECT
    o.customer_id,
    ROUND(SUM({REVENUE_EXPR}), 2) AS total_order_value
FROM order_items oi
JOIN orders o ON o.order_id = oi.order_id
WHERE o.customer_id IS NOT NULL AND o.customer_id != ''
GROUP BY o.customer_id
ORDER BY total_order_value DESC
LIMIT 10;
"""

QUERIES["3_monthly_order_count_last_12m"] = """
SELECT
    strftime('%Y-%m', order_date) AS year_month,
    COUNT(*) AS order_count
FROM orders
WHERE order_date >= date((SELECT MAX(order_date) FROM orders), '-12 months')
GROUP BY year_month
ORDER BY year_month;
"""


QUERIES["4_customers_never_delivered"] = """
SELECT DISTINCT o.customer_id
FROM orders o
WHERE o.customer_id IS NOT NULL AND o.customer_id != ''
  AND o.customer_id NOT IN (
      SELECT customer_id FROM orders
      WHERE status = 'DELIVERED' AND customer_id IS NOT NULL AND customer_id != ''
  );
"""

QUERIES["5_products_more_returns_than_purchases"] = """
SELECT
    p.product_id,
    p.product_name,
    SUM(CASE WHEN oi.quantity > 0 THEN oi.quantity ELSE 0 END) AS purchased_qty,
    SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END) AS returned_qty
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name
HAVING returned_qty > purchased_qty
ORDER BY returned_qty DESC;
"""

QUERIES["6_return_rate_per_category"] = """
SELECT
    p.category,
    SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END) AS returned_items,
    SUM(ABS(oi.quantity)) AS total_items,
    ROUND(
        1.0 * SUM(CASE WHEN oi.quantity < 0 THEN -oi.quantity ELSE 0 END)
        / NULLIF(SUM(ABS(oi.quantity)), 0), 4
    ) AS return_rate
FROM order_items oi
JOIN products p ON p.product_id = oi.product_id
GROUP BY p.category
ORDER BY return_rate DESC;
"""

QUERIES["7_running_total_revenue_per_region"] = f"""
WITH daily AS (
    SELECT
        o.region_code,
        date(o.order_date) AS order_date,
        SUM({REVENUE_EXPR}) AS daily_revenue
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    GROUP BY o.region_code, date(o.order_date)
)
SELECT
    region_code,
    order_date,
    ROUND(daily_revenue, 2) AS daily_revenue,
    ROUND(SUM(daily_revenue) OVER (
        PARTITION BY region_code ORDER BY order_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 2) AS running_total
FROM daily
ORDER BY region_code, order_date;
"""

QUERIES["8_dense_rank_products_by_revenue"] = f"""
WITH product_revenue AS (
    SELECT
        p.category,
        p.product_name,
        SUM({REVENUE_EXPR}) AS total_revenue
    FROM order_items oi
    JOIN products p ON p.product_id = oi.product_id
    GROUP BY p.category, p.product_name
)
SELECT
    category,
    product_name,
    ROUND(total_revenue, 2) AS total_revenue,
    DENSE_RANK() OVER (PARTITION BY category ORDER BY total_revenue DESC) AS rank_in_category
FROM product_revenue
ORDER BY category, rank_in_category;
"""

QUERIES["9_lag_days_between_orders"] = """
WITH customer_orders AS (
    SELECT customer_id, order_date
    FROM orders
    WHERE customer_id IS NOT NULL AND customer_id != ''
),
gaps AS (
    SELECT
        customer_id,
        order_date,
        LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date) AS previous_order_date,
        julianday(order_date) - julianday(
            LAG(order_date) OVER (PARTITION BY customer_id ORDER BY order_date)
        ) AS days_gap
    FROM customer_orders
)
SELECT
    customer_id,
    order_date,
    previous_order_date,
    ROUND(days_gap, 1) AS days_gap,
    CASE WHEN avg_gap > 30 THEN 'At Risk' ELSE 'Active' END AS risk_flag
FROM gaps
JOIN (
    SELECT customer_id, AVG(days_gap) AS avg_gap
    FROM gaps
    WHERE days_gap IS NOT NULL
    GROUP BY customer_id
) avgs USING (customer_id)
ORDER BY customer_id, order_date;
"""

QUERIES["10_cte_customer_revenue_tiers"] = f"""
WITH monthly_customer_revenue AS (
    SELECT
        o.customer_id,
        strftime('%Y-%m', o.order_date) AS year_month,
        SUM({REVENUE_EXPR}) AS revenue
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    WHERE o.customer_id IS NOT NULL AND o.customer_id != ''
    GROUP BY o.customer_id, year_month
),
tiered AS (
    SELECT
        customer_id,
        year_month,
        revenue,
        CASE
            WHEN revenue > 10000 THEN 'High'
            WHEN revenue >= 5000 THEN 'Medium'
            ELSE 'Low'
        END AS tier
    FROM monthly_customer_revenue
)
SELECT
    year_month,
    tier,
    COUNT(*) AS customer_count
FROM tiered
GROUP BY year_month, tier
ORDER BY year_month, tier;
"""

QUERIES["11_ntile_customer_quartiles"] = f"""
WITH customer_ltv AS (
    SELECT
        o.customer_id,
        SUM({REVENUE_EXPR}) AS total_value
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    WHERE o.customer_id IS NOT NULL AND o.customer_id != ''
    GROUP BY o.customer_id
)
SELECT
    customer_id,
    ROUND(total_value, 2) AS total_value,
    NTILE(4) OVER (ORDER BY total_value DESC) AS quartile,
    CASE NTILE(4) OVER (ORDER BY total_value DESC)
        WHEN 1 THEN 'Platinum'
        WHEN 2 THEN 'Gold'
        WHEN 3 THEN 'Silver'
        WHEN 4 THEN 'Bronze'
    END AS quartile_label
FROM customer_ltv
ORDER BY total_value DESC;
"""

QUERIES["12_yoy_comparison"] = f"""
WITH monthly_revenue AS (
    SELECT
        CAST(strftime('%Y', o.order_date) AS INTEGER) AS year,
        CAST(strftime('%m', o.order_date) AS INTEGER) AS month,
        SUM({REVENUE_EXPR}) AS revenue
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    GROUP BY year, month
)
SELECT
    cur.year,
    cur.month,
    ROUND(cur.revenue, 2) AS revenue,
    ROUND(prev.revenue, 2) AS prev_year_revenue,
    CASE
        WHEN prev.revenue IS NULL OR prev.revenue = 0 THEN NULL
        ELSE ROUND(100.0 * (cur.revenue - prev.revenue) / prev.revenue, 2)
    END AS yoy_growth_percent
FROM monthly_revenue cur
LEFT JOIN monthly_revenue prev
    ON prev.year = cur.year - 1 AND prev.month = cur.month
ORDER BY cur.year, cur.month;
"""

QUERIES["13_first_last_category"] = """
WITH customer_category_orders AS (
    SELECT
        o.customer_id,
        p.category,
        o.order_date,
        ROW_NUMBER() OVER (PARTITION BY o.customer_id ORDER BY o.order_date ASC) AS rn_first,
        ROW_NUMBER() OVER (PARTITION BY o.customer_id ORDER BY o.order_date DESC) AS rn_last
    FROM orders o
    JOIN order_items oi ON oi.order_id = o.order_id
    JOIN products p ON p.product_id = oi.product_id
    WHERE o.customer_id IS NOT NULL AND o.customer_id != ''
)
SELECT
    f.customer_id,
    f.category AS first_category,
    l.category AS last_category,
    CASE WHEN f.category != l.category THEN 'Yes' ELSE 'No' END AS category_shift
FROM (SELECT * FROM customer_category_orders WHERE rn_first = 1) f
JOIN (SELECT * FROM customer_category_orders WHERE rn_last = 1) l
    ON f.customer_id = l.customer_id
ORDER BY f.customer_id;
"""

QUERIES["14_cumulative_revenue_distribution"] = f"""
WITH customer_revenue AS (
    SELECT
        o.customer_id,
        SUM({REVENUE_EXPR}) AS revenue
    FROM order_items oi
    JOIN orders o ON o.order_id = oi.order_id
    WHERE o.customer_id IS NOT NULL AND o.customer_id != ''
    GROUP BY o.customer_id
),
ranked AS (
    SELECT
        customer_id,
        revenue,
        SUM(revenue) OVER (ORDER BY revenue DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_revenue,
        SUM(revenue) OVER () AS total_revenue
    FROM customer_revenue
)
SELECT
    customer_id,
    ROUND(revenue, 2) AS revenue,
    ROUND(cumulative_revenue, 2) AS cumulative_revenue,
    ROUND(100.0 * cumulative_revenue / total_revenue, 2) AS cumulative_percent
FROM ranked
ORDER BY revenue DESC;
"""

QUERIES["15_cohort_retention"] = """
WITH cohorts AS (
    SELECT
        customer_id,
        strftime('%Y-%m', registration_date) AS cohort_month
    FROM customers
),
customer_order_months AS (
    SELECT
        o.customer_id,
        c.cohort_month,
        (
            (CAST(strftime('%Y', o.order_date) AS INTEGER) - CAST(strftime('%Y', c.cohort_month || '-01') AS INTEGER)) * 12
            + (CAST(strftime('%m', o.order_date) AS INTEGER) - CAST(strftime('%m', c.cohort_month || '-01') AS INTEGER))
        ) AS month_offset
    FROM orders o
    JOIN cohorts c ON c.customer_id = o.customer_id
    WHERE o.customer_id IS NOT NULL AND o.customer_id != ''
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS cohort_size
    FROM cohorts
    GROUP BY cohort_month
)
SELECT
    com.cohort_month,
    com.month_offset,
    COUNT(DISTINCT com.customer_id) AS active_customers,
    cs.cohort_size,
    ROUND(100.0 * COUNT(DISTINCT com.customer_id) / cs.cohort_size, 2) AS retention_rate
FROM customer_order_months com
JOIN cohort_sizes cs ON cs.cohort_month = com.cohort_month
WHERE com.month_offset BETWEEN 0 AND 3
GROUP BY com.cohort_month, com.month_offset
ORDER BY com.cohort_month, com.month_offset;
"""

QUERIES["16_products_bought_together"] = """
SELECT
    pa.product_name AS product_a,
    pb.product_name AS product_b,
    COUNT(*) AS times_bought_together
FROM order_items a
JOIN order_items b
    ON a.order_id = b.order_id
    AND a.product_id < b.product_id
JOIN products pa ON pa.product_id = a.product_id
JOIN products pb ON pb.product_id = b.product_id
GROUP BY pa.product_name, pb.product_name
ORDER BY times_bought_together DESC
LIMIT 20;
"""


def run_all(db_path=DB_PATH, preview_rows=5):
    conn = sqlite3.connect(db_path)
    for name, sql in QUERIES.items():
        print(f"\n=== {name} ===")
        try:
            df = pd.read_sql_query(sql, conn)
            print(df.head(preview_rows).to_string(index=False))
            print(f"({len(df)} rows total)")
        except Exception as e:
            print(f"ERROR running query: {e}")
    conn.close()


if __name__ == "__main__":
    run_all()
