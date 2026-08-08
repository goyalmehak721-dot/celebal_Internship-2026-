

import sqlite3
import pandas as pd

DB_PATH = "ecommerce.db"


def main():
    conn = sqlite3.connect(DB_PATH)

    
    read_kwargs = dict(keep_default_na=False, na_values=[""])

    customers = pd.read_csv("customers_clean.csv", **read_kwargs)
    products = pd.read_csv("products_clean.csv", **read_kwargs)
    orders = pd.read_csv("orders_clean.csv", **read_kwargs)
    order_items = pd.read_csv("order_items_clean.csv", **read_kwargs)

    
    orders["order_date"] = pd.to_datetime(orders["order_date"]).dt.strftime("%Y-%m-%d %H:%M:%S")

    customers.to_sql("customers", conn, if_exists="replace", index=False)
    products.to_sql("products", conn, if_exists="replace", index=False)
    orders.to_sql("orders", conn, if_exists="replace", index=False)
    order_items.to_sql("order_items", conn, if_exists="replace", index=False)

    
    cur = conn.cursor()
    cur.execute("CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_items_order ON order_items(order_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_items_product ON order_items(product_id)")
    conn.commit()

    for table in ["customers", "products", "orders", "order_items"]:
        n = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table}: {n} rows loaded")

    conn.close()


if __name__ == "__main__":
    main()
