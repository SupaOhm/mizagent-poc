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
    (1, "Alex", "CEO", "Executive", "Corporate", None, "alex@mizuhada.example", "02-000-0001"),
    (2, "Jordan", "COO", "Executive", "Corporate", 1, "jordan@mizuhada.example", "02-000-0002"),
    # --- Corporate IT/AI team (Ohm lives here) ---
    (3, "Casey", "IT Manager", "IT/AI", "Corporate", 2, "casey@mizuhada.example", "02-000-0010"),
    (4, "Ohm", "Dev Intern", "IT/AI", "Corporate", 3, "ohm@mizuhada.example", "02-000-0011"),
    (5, "Morgan", "Data Analyst", "IT/AI", "Corporate", 3, "morgan@mizuhada.example", "02-000-0012"),

    # --- MizuMi brand ---
    (6, "Taylor", "Brand Lead", "Management", "MizuMi", 2, "taylor@mizuhada.example", "02-100-0001"),
    (7, "Sam", "Marketing Manager", "Marketing", "MizuMi", 6, "sam@mizuhada.example", "02-100-0002"),
    (8, "Riley", "Marketing Exec", "Marketing", "MizuMi", 7, "riley@mizuhada.example", "02-100-0003"),
    (9, "Quinn", "Warehouse Manager", "Warehouse", "MizuMi", 6, "quinn@mizuhada.example", "02-100-0010"),
    (10, "Avery", "Warehouse Staff", "Warehouse", "MizuMi", 9, "avery@mizuhada.example", "02-100-0011"),
    (11, "Drew", "Sales Manager", "Sales", "MizuMi", 6, "drew@mizuhada.example", "02-100-0020"),

    # --- Bomi brand ---
    (12, "Reese", "Brand Lead", "Management", "Bomi", 2, "reese@mizuhada.example", "02-200-0001"),
    (13, "Skyler", "Marketing Manager", "Marketing", "Bomi", 12, "skyler@mizuhada.example", "02-200-0002"),
    (14, "Parker", "Warehouse Manager", "Warehouse", "Bomi", 12, "parker@mizuhada.example", "02-200-0010"),
    (15, "Hayden", "Warehouse Staff", "Warehouse", "Bomi", 14, "hayden@mizuhada.example", "02-200-0011"),
    (16, "Rowan", "Sales Manager", "Sales", "Bomi", 12, "rowan@mizuhada.example", "02-200-0020"),
    (17, "Emerson", "Sales Exec", "Sales", "Bomi", 16, "emerson@mizuhada.example", "02-200-0021"),

    # --- GS brand ---
    (18, "Finley", "Brand Lead", "Management", "GS", 2, "finley@mizuhada.example", "02-300-0001"),
    (19, "Sage", "Marketing Manager", "Marketing", "GS", 18, "sage@mizuhada.example", "02-300-0002"),
    (20, "Blake", "Warehouse Manager", "Warehouse", "GS", 18, "blake@mizuhada.example", "02-300-0010"),
    (21, "Lane", "Warehouse Staff", "Warehouse", "GS", 20, "lane@mizuhada.example", "02-300-0011"),
    (22, "Marlow", "Sales Manager", "Sales", "GS", 18, "marlow@mizuhada.example", "02-300-0020"),
    (23, "Indi", "Sales Exec", "Sales", "GS", 22, "indi@mizuhada.example", "02-300-0021"),
]

# (sku, name, brand, category, current_stock, avg_daily_sales, reorder_point)
PRODUCTS = [
    # MizuMi
    ("MZ-SK-001", "MizuMi Hydra Serum", "MizuMi", "Skincare", 120, 8.0, 60),
    ("MZ-SK-002", "MizuMi Gentle Cleanser", "MizuMi", "Skincare", 30, 5.0, 50),   # low
    ("MZ-CO-001", "MizuMi Velvet Lipstick", "MizuMi", "Cosmetics", 200, 12.0, 80),
    ("MZ-CO-002", "MizuMi Glow Cushion", "MizuMi", "Cosmetics", 15, 9.0, 40),     # low
    ("MZ-WE-001", "MizuMi Collagen Drink", "MizuMi", "Wellness", 90, 0.0, 30),    # avg_daily_sales = 0 edge case
    # Bomi
    ("BM-SK-001", "Bomi Aqua Moisturizer", "Bomi", "Skincare", 75, 6.0, 50),
    ("BM-SK-002", "Bomi Clay Mask", "Bomi", "Skincare", 22, 4.0, 35),            # low
    ("BM-CO-001", "Bomi Matte Foundation", "Bomi", "Cosmetics", 140, 10.0, 70),
    ("BM-CO-002", "Bomi Brow Pencil", "Bomi", "Cosmetics", 18, 7.0, 45),         # low
    ("BM-WE-001", "Bomi Vitamin Gummies", "Bomi", "Wellness", 60, 3.0, 40),
    # GS
    ("GS-SK-001", "GS Repair Night Cream", "GS", "Skincare", 110, 7.0, 60),
    ("GS-CO-001", "GS Liquid Eyeliner", "GS", "Cosmetics", 25, 6.0, 50),         # low
    ("GS-CO-002", "GS Setting Powder", "GS", "Cosmetics", 95, 5.0, 40),
    ("GS-WE-001", "GS Protein Shake", "GS", "Wellness", 40, 8.0, 80),            # low
    ("GS-WE-002", "GS Sleep Tea", "GS", "Wellness", 130, 2.0, 30),
]

SCHEMA = """
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS employees;

CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    role        TEXT NOT NULL,
    team        TEXT NOT NULL,
    brand       TEXT NOT NULL,
    manager_id  INTEGER REFERENCES employees(employee_id),
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
