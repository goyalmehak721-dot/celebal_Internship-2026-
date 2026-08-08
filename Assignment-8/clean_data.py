

import re
import pandas as pd

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fix inconsistent date formats (YYYY-MM-DD HH:MM:SS or DD-MM-YYYY) and
    flag/handle NULL customer_ids. Returns a cleaned copy; does not mutate input.
    """
    df = df.copy()

    df["customer_id"] = df["customer_id"].replace("", pd.NA)
    df["customer_id_missing"] = df["customer_id"].isna()

    parsed_iso = pd.to_datetime(df["order_date"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    parsed_dmy = pd.to_datetime(df["order_date"], format="%d-%m-%Y", errors="coerce")
    df["order_date_clean"] = parsed_iso.fillna(parsed_dmy)
    df["order_date_unparseable"] = df["order_date_clean"].isna()

    df["order_date"] = df["order_date_clean"]
    df = df.drop(columns=["order_date_clean"])

    return df


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize product_name: trim whitespace and apply title case."""
    df = df.copy()
    df["product_name"] = df["product_name"].astype(str).str.strip().str.title()
    return df


def validate_emails(df: pd.DataFrame) -> list:
    """Return list of customer_ids whose email fails a basic format check."""
    invalid_mask = ~df["email"].astype(str).str.match(EMAIL_RE)
    return df.loc[invalid_mask, "customer_id"].tolist()


def check_referential_integrity(order_items_df: pd.DataFrame, orders_df: pd.DataFrame) -> pd.DataFrame:
    """Return order_items rows whose order_id does not exist in orders."""
    valid_ids = set(orders_df["order_id"])
    bad_mask = ~order_items_df["order_id"].isin(valid_ids)
    return order_items_df.loc[bad_mask]


def main():
    
    read_kwargs = dict(keep_default_na=False, na_values=[""])

    orders_raw = pd.read_csv("orders.csv", dtype={"customer_id": "string"}, **read_kwargs)
    products_raw = pd.read_csv("products.csv", **read_kwargs)
    order_items_raw = pd.read_csv("order_items.csv", **read_kwargs)
    customers_raw = pd.read_csv("customers.csv", **read_kwargs)

    orders_clean = clean_orders(orders_raw)
    products_clean = clean_products(products_raw)
    invalid_email_ids = validate_emails(customers_raw)
    bad_items = check_referential_integrity(order_items_raw, orders_raw)

    orders_clean.to_csv("orders_clean.csv", index=False)
    products_clean.to_csv("products_clean.csv", index=False)
    customers_raw.to_csv("customers_clean.csv", index=False)  
    order_items_raw.to_csv("order_items_clean.csv", index=False)

   
    report_lines = [
        "DATA QUALITY ISSUES REPORT",
        "=" * 40,
        f"Orders with missing customer_id: {int(orders_clean['customer_id_missing'].sum())}",
        f"Orders with unparseable order_date: {int(orders_clean['order_date_unparseable'].sum())}",
        f"Customers with invalid emails: {len(invalid_email_ids)}",
        f"  -> IDs: {invalid_email_ids[:20]}{' ...' if len(invalid_email_ids) > 20 else ''}",
        f"order_items referencing non-existent orders: {len(bad_items)}",
        f"order_items with negative quantity (returns): {int((order_items_raw['quantity'] < 0).sum())}",
        f"order_items with discount_percent > 100: {int((order_items_raw['discount_percent'] > 100).sum())}",
    ]
    report = "\n".join(report_lines)
    with open("issues_report.txt", "w") as f:
        f.write(report)

    print(report)


if __name__ == "__main__":
    main()
