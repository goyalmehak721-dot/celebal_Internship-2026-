

import csv
import random
from datetime import datetime, timedelta

random.seed(42)  

FIRST_NAMES = [
    "Aarav", "Priya", "Rohan", "Ananya", "Vikram", "Sneha", "Karan", "Isha",
    "Arjun", "Neha", "Rahul", "Divya", "Aditya", "Pooja", "Sanjay", "Kavya",
    "Amit", "Riya", "Nikhil", "Meera", "John", "Emma", "Liam", "Olivia",
    "Noah", "Ava", "William", "Sophia", "James", "Isabella"
]
LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Patel", "Kumar", "Singh", "Reddy", "Nair",
    "Iyer", "Menon", "Rao", "Das", "Chopra", "Malhotra", "Kapoor", "Joshi",
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis"
]
CUSTOMER_TYPES = ["REGULAR", "PREMIUM", "VIP"]
CUSTOMER_TYPE_WEIGHTS = [0.7, 0.22, 0.08]

CATEGORIES = {
    "Electronics": ["Mobiles", "Laptops", "Accessories", "Audio", "Cameras"],
    "Clothing": ["Men", "Women", "Kids", "Footwear", "Winterwear"],
    "Home": ["Kitchen", "Furniture", "Decor", "Bedding", "Storage"],
    "Books": ["Fiction", "Non-Fiction", "Comics", "Academic", "Children"],
}
PRODUCT_NOUNS = [
    "Wireless Headphones", "Bluetooth Speaker", "Running Shoes", "Cotton T-Shirt",
    "Steel Water Bottle", "Yoga Mat", "Table Lamp", "Novel", "Notebook Set",
    "Kitchen Knife", "Backpack", "Smart Watch", "Desk Organizer", "Coffee Mug",
    "Denim Jacket", "Bed Sheet Set", "Comic Bundle", "Cookbook", "Phone Case",
    "Laptop Stand", "Wall Clock", "Sneakers", "Winter Scarf", "Study Lamp",
]

STATUSES = ["PLACED", "SHIPPED", "DELIVERED", "CANCELLED", "RETURNED"]
STATUS_WEIGHTS = [0.15, 0.15, 0.55, 0.08, 0.07]

REGION_CODES = ["NA", "EU", "APAC", "LATAM", "MEA"]

N_CUSTOMERS = 600
N_PRODUCTS = 150
N_ORDERS = 1500
N_ORDER_ITEMS = 3500

START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 12, 31)


def random_datetime(start=START_DATE, end=END_DATE):
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


def maybe_messy_email(name, idx, make_invalid):
    base = name.lower().replace(" ", ".")
    domain = random.choice(["gmail.com", "yahoo.com", "outlook.com", "company.com"])
    if make_invalid:
        
        if random.random() < 0.5:
            return f"{base}{domain}"         
        else:
            return f"{base}@"                 
    return f"{base}{idx}@{domain}"


def messy_product_name(name):
    """Randomly add extra spaces and/or mixed case to a product name."""
    variant = name
    r = random.random()
    if r < 0.15:
        variant = "  " + variant + "   "        
    if r < 0.10:
        variant = variant.upper()
    elif 0.10 <= r < 0.20:
        variant = variant.lower()
    return variant



def generate_customers():
    rows = []
    invalid_email_idx = set(random.sample(range(1, N_CUSTOMERS + 1),
                                           k=int(N_CUSTOMERS * 0.02)))
    for cid in range(1, N_CUSTOMERS + 1):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        email = maybe_messy_email(name, cid, cid in invalid_email_idx)
        reg_date = random_datetime(START_DATE, END_DATE - timedelta(days=30))
        ctype = random.choices(CUSTOMER_TYPES, weights=CUSTOMER_TYPE_WEIGHTS)[0]
        rows.append({
            "customer_id": cid,
            "customer_name": name,
            "email": email,
            "registration_date": reg_date.strftime("%Y-%m-%d %H:%M:%S"),
            "customer_type": ctype,
        })
    return rows

def generate_products():
    rows = []
    for pid in range(1, N_PRODUCTS + 1):
        category = random.choice(list(CATEGORIES.keys()))
        subcategory = random.choice(CATEGORIES[category])
        base_name = random.choice(PRODUCT_NOUNS)
        product_name = messy_product_name(f"{base_name} {random.choice(['Pro','Lite','Plus','Max',''])}".strip())
        cost_price = round(random.uniform(5, 500), 2)
        rows.append({
            "product_id": pid,
            "product_name": product_name,
            "category": category,
            "subcategory": subcategory,
            "cost_price": cost_price,
        })
    return rows



def generate_orders(customer_ids):
    rows = []
    null_customer_idx = set(random.sample(range(1, N_ORDERS + 1),
                                           k=int(N_ORDERS * 0.05)))
    wrong_format_idx = set(random.sample(range(1, N_ORDERS + 1),
                                          k=int(N_ORDERS * 0.08)))
    order_ids = []
    for oid in range(1, N_ORDERS + 1):
        cust_id = "" if oid in null_customer_idx else random.choice(customer_ids)
        odate = random_datetime()
        if oid in wrong_format_idx:
            date_str = odate.strftime("%d-%m-%Y")  
        else:
            date_str = odate.strftime("%Y-%m-%d %H:%M:%S")
        status = random.choices(STATUSES, weights=STATUS_WEIGHTS)[0]
        region = random.choice(REGION_CODES)
        rows.append({
            "order_id": oid,
            "customer_id": cust_id,
            "order_date": date_str,
            "status": status,
            "region_code": region,
        })
        order_ids.append(oid)
    return rows, order_ids


def generate_order_items(order_ids, product_ids):
    rows = []
    negative_qty_idx = set(random.sample(range(1, N_ORDER_ITEMS + 1),
                                          k=int(N_ORDER_ITEMS * 0.03)))
    for item_id in range(1, N_ORDER_ITEMS + 1):
        order_id = random.choice(order_ids)  
        product_id = random.choice(product_ids)
        quantity = random.randint(1, 6)
        if item_id in negative_qty_idx:
            quantity = -quantity  # a return
        unit_price = round(random.uniform(5, 600), 2)
        discount_percent = round(random.uniform(0, 40), 1)
        rows.append({
            "item_id": item_id,
            "order_id": order_id,
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": unit_price,
            "discount_percent": discount_percent,
        })
    return rows


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows -> {path}")


def main():
    customers = generate_customers()
    products = generate_products()
    orders, order_ids = generate_orders([c["customer_id"] for c in customers])
    order_items = generate_order_items(order_ids, [p["product_id"] for p in products])

    write_csv("customers.csv", customers,
              ["customer_id", "customer_name", "email", "registration_date", "customer_type"])
    write_csv("products.csv", products,
              ["product_id", "product_name", "category", "subcategory", "cost_price"])
    write_csv("orders.csv", orders,
              ["order_id", "customer_id", "order_date", "status", "region_code"])
    write_csv("order_items.csv", order_items,
              ["item_id", "order_id", "product_id", "quantity", "unit_price", "discount_percent"])


if __name__ == "__main__":
    main()
