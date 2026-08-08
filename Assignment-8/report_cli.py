

import sqlite3
import sys
import argparse
from datetime import datetime, timedelta

DB_PATH = "ecommerce.db"

REVENUE_EXPR = "oi.quantity * oi.unit_price * (1 - oi.discount_percent/100.0)"


def get_period_summary(conn, start_date, end_date):
    """Return dict with total_orders, revenue, unique_customers, top_3_products
    for orders with order_date in [start_date, end_date)."""
    cur = conn.cursor()

    cur.execute(f"""
        SELECT
            COUNT(DISTINCT o.order_id) AS total_orders,
            COALESCE(SUM({REVENUE_EXPR}), 0) AS revenue,
            COUNT(DISTINCT o.customer_id) AS unique_customers
        FROM orders o
        LEFT JOIN order_items oi ON oi.order_id = o.order_id
        WHERE o.order_date >= ? AND o.order_date < ?
    """, (start_date, end_date))
    total_orders, revenue, unique_customers = cur.fetchone()

    cur.execute(f"""
        SELECT p.product_name, SUM({REVENUE_EXPR}) AS product_revenue
        FROM order_items oi
        JOIN orders o ON o.order_id = oi.order_id
        JOIN products p ON p.product_id = oi.product_id
        WHERE o.order_date >= ? AND o.order_date < ?
        GROUP BY p.product_name
        ORDER BY product_revenue DESC
        LIMIT 3
    """, (start_date, end_date))
    top_products = cur.fetchall()

    return {
        "total_orders": total_orders or 0,
        "revenue": revenue or 0.0,
        "unique_customers": unique_customers or 0,
        "top_products": top_products,
    }


def previous_period(start_date, end_date):
    """Given [start, end), return the immediately preceding period of equal length."""
    fmt = "%Y-%m-%d"
    start = datetime.strptime(start_date, fmt)
    end = datetime.strptime(end_date, fmt)
    length = end - start
    prev_end = start
    prev_start = start - length
    return prev_start.strftime(fmt), prev_end.strftime(fmt)


def pct_change(current, previous):
    if previous in (0, None):
        return None
    return round(100.0 * (current - previous) / previous, 2)


def date_range_for_report_type(report_type, anchor_date=None):
    """Compute a default [start, end) window for daily/weekly/monthly, ending at anchor_date."""
    fmt = "%Y-%m-%d"
    end = datetime.strptime(anchor_date, fmt) if anchor_date else datetime.today()
    if report_type == "daily":
        start = end - timedelta(days=1)
    elif report_type == "weekly":
        start = end - timedelta(days=7)
    elif report_type == "monthly":
        start = end - timedelta(days=30)
    else:
        raise ValueError("report_type must be daily, weekly, or monthly")
    return start.strftime(fmt), end.strftime(fmt)


def print_report(report_type, start_date, end_date, conn):
    current = get_period_summary(conn, start_date, end_date)
    prev_start, prev_end = previous_period(start_date, end_date)
    previous = get_period_summary(conn, prev_start, prev_end)

    print("\n" + "=" * 50)
    print(f"{report_type.upper()} REPORT: {start_date} to {end_date}")
    print("=" * 50)
    print(f"Total Orders:      {current['total_orders']}"
          f"  ({pct_change(current['total_orders'], previous['total_orders'])}% vs previous period)")
    print(f"Revenue:           {current['revenue']:.2f}"
          f"  ({pct_change(current['revenue'], previous['revenue'])}% vs previous period)")
    print(f"Unique Customers:  {current['unique_customers']}"
          f"  ({pct_change(current['unique_customers'], previous['unique_customers'])}% vs previous period)")
    print("\nTop 3 Products:")
    if current["top_products"]:
        for name, rev in current["top_products"]:
            print(f"  - {name}: {rev:.2f}")
    else:
        print("  (no sales in this period)")
    print(f"\nPrevious period: {prev_start} to {prev_end}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="E-commerce summary report generator")
    parser.add_argument("--type", choices=["daily", "weekly", "monthly"], help="Report type")
    parser.add_argument("--start", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", help="End date YYYY-MM-DD")
    parser.add_argument("--db", default=DB_PATH, help="Path to SQLite database")
    args = parser.parse_args()

    report_type = args.type
    start_date = args.start
    end_date = args.end

    if report_type is None:
        report_type = input("Report type (daily/weekly/monthly): ").strip().lower()
        while report_type not in ("daily", "weekly", "monthly"):
            report_type = input("Please enter daily, weekly, or monthly: ").strip().lower()

    if start_date is None or end_date is None:
        use_custom = input("Enter custom date range? (y/n): ").strip().lower()
        if use_custom == "y":
            start_date = input("Start date (YYYY-MM-DD): ").strip()
            end_date = input("End date (YYYY-MM-DD): ").strip()
        else:
            start_date, end_date = date_range_for_report_type(report_type)

    conn = sqlite3.connect(args.db)
    try:
        print_report(report_type, start_date, end_date, conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
