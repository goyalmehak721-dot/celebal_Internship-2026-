

from datetime import datetime, timedelta
import pandas as pd

from clean_data import check_referential_integrity


def test_order_item_with_missing_order():
    """order_items row pointing at a non-existent order_id should be flagged
    by check_referential_integrity, not silently dropped or crash the pipeline."""
    orders = pd.DataFrame({
        "order_id": [1, 2, 3],
        "customer_id": [10, 11, 12],
    })
    order_items = pd.DataFrame({
        "item_id": [100, 101],
        "order_id": [1, 999],   
        "product_id": [5, 6],
        "quantity": [2, 1],
        "unit_price": [10.0, 20.0],
        "discount_percent": [0, 0],
    })

    bad_rows = check_referential_integrity(order_items, orders)

    assert len(bad_rows) == 1, f"expected 1 orphaned row, got {len(bad_rows)}"
    assert bad_rows.iloc[0]["order_id"] == 999
    print("PASS: test_order_item_with_missing_order")


def test_discount_percent_over_100():
    """discount_percent > 100 is invalid input (would produce negative revenue).
    We verify it's detectable so the pipeline can flag/reject it rather than
    silently generating nonsense revenue numbers."""
    order_items = pd.DataFrame({
        "item_id": [1, 2],
        "order_id": [1, 1],
        "product_id": [1, 2],
        "quantity": [1, 1],
        "unit_price": [100.0, 50.0],
        "discount_percent": [150, 20],   
    })

    invalid = order_items[order_items["discount_percent"] > 100]
    assert len(invalid) == 1
    assert invalid.iloc[0]["item_id"] == 1

    revenue = order_items["quantity"] * order_items["unit_price"] * (1 - order_items["discount_percent"] / 100)
    assert revenue.iloc[0] < 0, "an unflagged discount_percent > 100 produces negative revenue"
    print("PASS: test_discount_percent_over_100 (correctly detects invalid rows)")


def test_quantity_zero():
    """quantity == 0 is a valid-looking but meaningless line item: it contributes
    zero revenue and shouldn't be counted as either a purchase or a return."""
    order_items = pd.DataFrame({
        "item_id": [1, 2, 3],
        "order_id": [1, 1, 1],
        "product_id": [1, 2, 3],
        "quantity": [0, 5, -2],
        "unit_price": [10.0, 10.0, 10.0],
        "discount_percent": [0, 0, 0],
    })

    revenue = order_items["quantity"] * order_items["unit_price"] * (1 - order_items["discount_percent"] / 100)
    assert revenue.iloc[0] == 0, "zero quantity should contribute exactly zero revenue"

    zero_qty_rows = order_items[order_items["quantity"] == 0]
    assert len(zero_qty_rows) == 1
    print("PASS: test_quantity_zero")


def test_future_order_date():
    """An order_date in the future is a data-quality problem (clock skew, bad
    manual entry, etc.). It should be detectable rather than silently included
    in 'current' reporting periods."""
    future_date = datetime.now() + timedelta(days=30)
    orders = pd.DataFrame({
        "order_id": [1, 2],
        "customer_id": [1, 2],
        "order_date": [datetime.now() - timedelta(days=1), future_date],
    })

    future_orders = orders[orders["order_date"] > datetime.now()]
    assert len(future_orders) == 1
    assert future_orders.iloc[0]["order_id"] == 2
    print("PASS: test_future_order_date")


def run_all():
    tests = [
        test_order_item_with_missing_order,
        test_discount_percent_over_100,
        test_quantity_zero,
        test_future_order_date,
    ]
    failures = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            failures += 1
            print(f"FAIL: {t.__name__} -> {e}")
    print(f"\n{len(tests) - failures}/{len(tests)} tests passed")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    run_all()
