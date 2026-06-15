"""Seed a mock SQLite database for the Mizuhada Internal AI Agent POC (Project 2).

Creates mock_company.db with two tables (employees, products) and inserts
fictional seed data. All employee names are generic placeholders EXCEPT "Ohm"
(the intern building this). No real people's names appear here.

Run:  python seed_db.py
"""

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "mock_company.db")

# (employee_id, name, role, team, brand, manager_id, email, phone)
EMPLOYEES = [
    # --- Corporate leadership (top of hierarchy, manager_id = NULL) ---
    ("E001", "Alex", "CEO", "Executive", "Corporate", None, "alex@mizahaha.example", "02-000-0001"),
    ("E002", "Jordan", "COO", "Executive", "Corporate", "E001", "jordan@mizahaha.example", "02-000-0002"),
    # --- Corporate IT/AI team (Ohm lives here) ---
    ("E003", "Casey", "IT Manager", "IT/AI", "Corporate", "E002", "casey@mizahaha.example", "02-000-0010"),
    ("E004", "Ohm", "Dev Intern", "IT/AI", "Corporate", "E003", "ohm@mizahaha.example", "02-000-0011"),
    ("E005", "Morgan", "Data Analyst", "IT/AI", "Corporate", "E003", "morgan@mizahaha.example", "02-000-0012"),

    # --- Mihihi brand ---
    ("E006", "Taylor", "Brand Lead", "Management", "Mihihi", "E002", "taylor@mizahaha.example", "02-100-0001"),
    ("E007", "Sam", "Marketing Manager", "Marketing", "Mihihi", "E006", "sam@mizahaha.example", "02-100-0002"),
    ("E008", "Riley", "Marketing Exec", "Marketing", "Mihihi", "E007", "riley@mizahaha.example", "02-100-0003"),
    ("E009", "Quinn", "Warehouse Manager", "Warehouse", "Mihihi", "E006", "quinn@mizahaha.example", "02-100-0010"),
    ("E010", "Avery", "Warehouse Staff", "Warehouse", "Mihihi", "E009", "avery@mizahaha.example", "02-100-0011"),
    ("E011", "Drew", "Sales Manager", "Sales", "Mihihi", "E006", "drew@mizahaha.example", "02-100-0020"),

    # --- Bobi brand ---
    ("E012", "Reese", "Brand Lead", "Management", "Bobi", "E002", "reese@mizahaha.example", "02-200-0001"),
    ("E013", "Skyler", "Marketing Manager", "Marketing", "Bobi", "E012", "skyler@mizahaha.example", "02-200-0002"),
    ("E014", "Parker", "Warehouse Manager", "Warehouse", "Bobi", "E012", "parker@mizahaha.example", "02-200-0010"),
    ("E015", "Hayden", "Warehouse Staff", "Warehouse", "Bobi", "E014", "hayden@mizahaha.example", "02-200-0011"),
    ("E016", "Rowan", "Sales Manager", "Sales", "Bobi", "E012", "rowan@mizahaha.example", "02-200-0020"),
    ("E017", "Emerson", "Sales Exec", "Sales", "Bobi", "E016", "emerson@mizahaha.example", "02-200-0021"),

    # --- Harshcolor brand ---
    ("E018", "Finley", "Brand Lead", "Management", "Harshcolor", "E002", "finley@mizahaha.example", "02-300-0001"),
    ("E019", "Sage", "Marketing Manager", "Marketing", "Harshcolor", "E018", "sage@mizahaha.example", "02-300-0002"),
    ("E020", "Blake", "Warehouse Manager", "Warehouse", "Harshcolor", "E018", "blake@mizahaha.example", "02-300-0010"),
    ("E021", "Lane", "Warehouse Staff", "Warehouse", "Harshcolor", "E020", "lane@mizahaha.example", "02-300-0011"),
    ("E022", "Marlow", "Sales Manager", "Sales", "Harshcolor", "E018", "marlow@mizahaha.example", "02-300-0020"),
    ("E023", "Indi", "Sales Exec", "Sales", "Harshcolor", "E022", "indi@mizahaha.example", "02-300-0021"),
]

# (sku, name, brand, category, current_stock, avg_daily_sales, reorder_point)
PRODUCTS = [
    # Mihihi -> Skincare / sunscreen brand only
    ("MH-SK-001", "Facial Sunscreen SPF50", "Mihihi", "Skincare", 110, 7.0, 60),
    ("MH-SK-002", "Hydrating Serum", "Mihihi", "Skincare", 30, 5.0, 50),         # low
    ("MH-SK-003", "Balancing Toner", "Mihihi", "Skincare", 75, 6.0, 50),
    ("MH-SK-004", "Gentle Facial Cleanser", "Mihihi", "Skincare", 20, 4.0, 45),  # low
    ("MH-SK-005", "Calming Sheet Mask", "Mihihi", "Skincare", 90, 0.0, 30),      # avg_daily_sales = 0 edge case
    # Bobi -> Wellness / supplement brand only
    ("BB-WL-001", "Collagen Powder", "Bobi", "Wellness", 60, 3.0, 40),
    ("BB-WL-002", "Probiotic Capsules", "Bobi", "Wellness", 15, 5.0, 40),        # low
    ("BB-WL-003", "Vitamin C Effervescent", "Bobi", "Wellness", 18, 7.0, 45),    # low
    ("BB-WL-004", "Sleep Support Capsules", "Bobi", "Wellness", 130, 2.0, 30),
    ("BB-WL-005", "Electrolyte Mix", "Bobi", "Wellness", 40, 8.0, 80),           # low
    # Harshcolor -> Cosmetics / makeup brand only
    ("HC-CO-001", "Matte Foundation", "Harshcolor", "Cosmetics", 140, 10.0, 70),
    ("HC-CO-002", "Lip Tint", "Harshcolor", "Cosmetics", 25, 6.0, 50),          # low
    ("HC-CO-003", "Eyeshadow Palette", "Harshcolor", "Cosmetics", 200, 12.0, 80),
    ("HC-CO-004", "Volumizing Mascara", "Harshcolor", "Cosmetics", 18, 7.0, 45), # low
    ("HC-CO-005", "Blush Compact", "Harshcolor", "Cosmetics", 95, 5.0, 40),
]

SCHEMA = """
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS employees;

CREATE TABLE employees (
    employee_id TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    role        TEXT NOT NULL,
    team        TEXT NOT NULL,
    brand       TEXT NOT NULL,
    manager_id  TEXT REFERENCES employees(employee_id),
    email       TEXT,
    phone       TEXT
);

CREATE TABLE products (
    sku             TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    brand           TEXT NOT NULL,
    category        TEXT NOT NULL,
    current_stock   INTEGER NOT NULL,
    avg_daily_sales REAL NOT NULL,
    reorder_point   INTEGER NOT NULL
);
"""


def seed():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA)
        conn.executemany(
            "INSERT INTO employees "
            "(employee_id, name, role, team, brand, manager_id, email, phone) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            EMPLOYEES,
        )
        conn.executemany(
            "INSERT INTO products "
            "(sku, name, brand, category, current_stock, avg_daily_sales, reorder_point) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            PRODUCTS,
        )
        conn.commit()

        emp_count = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        prod_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        print(f"Seeded {DB_PATH}")
        print(f"  employees: {emp_count} rows")
        print(f"  products:  {prod_count} rows")
    finally:
        conn.close()


if __name__ == "__main__":
    seed()
