import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    segment TEXT NOT NULL,
    region TEXT NOT NULL,
    loyalty_points INTEGER NOT NULL,
    account_age_days INTEGER NOT NULL,
    credit_limit REAL NOT NULL,
    account_status TEXT NOT NULL
);
CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_cost REAL NOT NULL,
    supplier_tier TEXT NOT NULL
);
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    order_date TEXT NOT NULL,
    status TEXT NOT NULL,
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    discount_rate REAL NOT NULL,
    returned_quantity INTEGER NOT NULL,
    shipping_fee REAL NOT NULL,
    FOREIGN KEY(customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY(product_id) REFERENCES products(product_id)
);
CREATE TABLE rebate_policies (
    policy_id TEXT PRIMARY KEY,
    segment TEXT NOT NULL,
    region TEXT NOT NULL,
    min_net_revenue REAL NOT NULL,
    rebate_rate REAL NOT NULL,
    effective_from TEXT NOT NULL,
    effective_to TEXT NOT NULL
);
"""

CUSTOMERS = [
    ("C1001", "Acme Precision", "GOLD", "EAST", 4200, 860, 80000, "ACTIVE"),
    ("C1002", "Northwind Tools", "SILVER", "NORTH", 2100, 530, 50000, "ACTIVE"),
    ("C1003", "Delta Works", "PLATINUM", "WEST", 7100, 1240, 120000, "ACTIVE"),
]
PRODUCTS = [
    ("P100", "Servo Drive", "Automation", 310.00, "A"),
    ("P200", "Linear Guide", "Motion", 88.00, "B"),
    ("P300", "Safety Relay", "Electrical", 42.00, "A"),
    ("P400", "Tool Holder", "Tooling", 65.00, "C"),
    ("P500", "Vision Sensor", "Inspection", 155.00, "A"),
]
ORDERS = [
    ("O1001", "C1001", "2026-04-03", "COMPLETED", "P100", 10, 520.00, 0.05, 0, 35.00),
    ("O1002", "C1001", "2026-04-18", "COMPLETED", "P200", 50, 145.00, 0.10, 5, 20.00),
    ("O1003", "C1001", "2026-05-08", "COMPLETED", "P300", 80, 75.00, 0.00, 24, 18.00),
    ("O1004", "C1001", "2026-05-21", "CANCELLED", "P400", 100, 120.00, 0.15, 0, 25.00),
    ("O1005", "C1001", "2026-06-11", "COMPLETED", "P500", 20, 260.00, 0.08, 2, 22.00),
    ("O1006", "C1001", "2026-07-02", "COMPLETED", "P100", 5, 530.00, 0.00, 0, 15.00),
    ("O2001", "C1002", "2026-05-05", "COMPLETED", "P200", 40, 140.00, 0.05, 0, 18.00),
    ("O3001", "C1003", "2026-04-12", "COMPLETED", "P100", 30, 510.00, 0.04, 1, 40.00),
]
POLICIES = [
    ("R1", "GOLD", "EAST", 10000.00, 0.03, "2026-01-01", "2026-12-31"),
    ("R2", "PLATINUM", "WEST", 15000.00, 0.05, "2026-01-01", "2026-12-31"),
    ("R3", "SILVER", "NORTH", 20000.00, 0.01, "2026-01-01", "2026-12-31"),
]


def build_database(path: str | Path) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?,?,?)", CUSTOMERS)
    conn.executemany("INSERT INTO products VALUES (?,?,?,?,?)", PRODUCTS)
    conn.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?,?)", ORDERS)
    conn.executemany("INSERT INTO rebate_policies VALUES (?,?,?,?,?,?,?)", POLICIES)
    conn.commit()
    return conn
