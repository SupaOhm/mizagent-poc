"""Read-only data-access tools for the Mizuhada Internal AI Agent POC (Project 2).

This is the ONLY module that knows about DB connection + schema details.
Swapping the mock SQLite for a real database later should touch ONLY this file;
the function signatures below are a stable contract the agent depends on.

All functions:
  * are side-effect-free (read-only SELECT queries),
  * return plain JSON-serializable dicts,
  * never raise on "not found" / bad input -> they return an error/found:false dict.
"""

import json
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "mock_company.db")


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _rows_to_dicts(rows):
    return [dict(r) for r in rows]


def search_employees(name=None, team=None):
    """Find employees by partial/case-insensitive name and/or exact team.

    At least one of name/team must be given (avoid full-table dumps).
    Returns: {count, results} or {error}.
    """
    if name is None and team is None:
        return {"error": "Provide at least one of 'name' or 'team'."}

    clauses, params = [], []
    if name is not None:
        clauses.append("LOWER(name) LIKE LOWER(?)")
        params.append(f"%{name}%")
    if team is not None:
        clauses.append("team = ?")
        params.append(team)

    sql = (
        "SELECT employee_id, name, role, team, brand, manager_id, email, phone "
        "FROM employees WHERE " + " AND ".join(clauses) + " ORDER BY employee_id"
    )
    conn = _connect()
    try:
        rows = _rows_to_dicts(conn.execute(sql, params).fetchall())
    finally:
        conn.close()
    return {"count": len(rows), "results": rows}


def get_employee_record(employee_id):
    """Full record for one employee, with manager_name resolved via self-join.

    Returns the record dict, or {found:false, error} if the id does not exist.
    """
    sql = """
        SELECT e.employee_id, e.name, e.role, e.team, e.brand,
               e.manager_id, m.name AS manager_name,
               e.email, e.phone
        FROM employees e
        LEFT JOIN employees m ON e.manager_id = m.employee_id
        WHERE e.employee_id = ?
    """
    conn = _connect()
    try:
        row = conn.execute(sql, (employee_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        return {"found": False, "error": f"No employee with employee_id={employee_id}."}
    record = dict(row)
    record["found"] = True
    return record


def query_products(brand=None, category=None, stock_status=None):
    """Filtered product lookup (pure passthrough, no computed metrics).

    stock_status: "low" (current_stock < reorder_point), "ok" (>=), or None.
    Returns: {count, results} or {error} for invalid stock_status.
    """
    clauses, params = [], []
    if brand is not None:
        clauses.append("brand = ?")
        params.append(brand)
    if category is not None:
        clauses.append("category = ?")
        params.append(category)
    if stock_status is not None:
        if stock_status == "low":
            clauses.append("current_stock < reorder_point")
        elif stock_status == "ok":
            clauses.append("current_stock >= reorder_point")
        else:
            return {"error": "stock_status must be 'low', 'ok', or omitted."}

    sql = (
        "SELECT sku, name, brand, category, current_stock, avg_daily_sales, "
        "reorder_point FROM products"
    )
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY sku"

    conn = _connect()
    try:
        rows = _rows_to_dicts(conn.execute(sql, params).fetchall())
    finally:
        conn.close()
    return {"count": len(rows), "results": rows}


def calculate_stock_coverage(sku):
    """Compute days_of_supply = current_stock / avg_daily_sales IN PYTHON.

    The ratio is computed here, never left to the LLM.
    avg_daily_sales == 0 -> days_of_supply: null + explanatory note.
    Unknown sku -> {found:false, error}.
    """
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT sku, name, brand, current_stock, avg_daily_sales, reorder_point "
            "FROM products WHERE sku = ?",
            (sku,),
        ).fetchone()
    finally:
        conn.close()
    if row is None:
        return {"found": False, "error": f"No product with sku={sku}."}

    p = dict(row)
    avg = p["avg_daily_sales"]
    result = {
        "found": True,
        "sku": p["sku"],
        "name": p["name"],
        "brand": p["brand"],
        "current_stock": p["current_stock"],
        "avg_daily_sales": avg,
        "reorder_point": p["reorder_point"],
    }
    if avg == 0:
        result["days_of_supply"] = None
        result["note"] = (
            "avg_daily_sales is 0; days_of_supply is undefined "
            "(no sales velocity to divide by)."
        )
    else:
        result["days_of_supply"] = round(p["current_stock"] / avg, 1)
    return result


def get_low_stock_items(brand=None):
    """All products where current_stock < reorder_point.

    Adds computed 'shortfall' = reorder_point - current_stock,
    sorted by shortfall descending. Optional brand filter.
    Returns: {count, results}.
    """
    sql = (
        "SELECT sku, name, brand, category, current_stock, avg_daily_sales, "
        "reorder_point, (reorder_point - current_stock) AS shortfall "
        "FROM products WHERE current_stock < reorder_point"
    )
    params = []
    if brand is not None:
        sql += " AND brand = ?"
        params.append(brand)
    sql += " ORDER BY shortfall DESC"

    conn = _connect()
    try:
        rows = _rows_to_dicts(conn.execute(sql, params).fetchall())
    finally:
        conn.close()
    return {"count": len(rows), "results": rows}


def _smoke_test():
    """Call every tool with realistic example args; pretty-print JSON."""
    def show(label, value):
        print(f"\n=== {label} ===")
        print(json.dumps(value, indent=2, ensure_ascii=False))

    show("search_employees(name='ohm')", search_employees(name="ohm"))
    show("search_employees(team='Warehouse')", search_employees(team="Warehouse"))
    show("search_employees() [error case]", search_employees())

    show("get_employee_record(4)  # Ohm", get_employee_record(4))
    show("get_employee_record(9999) [not found]", get_employee_record(9999))

    show("query_products(brand='MizuMi')", query_products(brand="MizuMi"))
    show("query_products(stock_status='low')", query_products(stock_status="low"))
    show("query_products(stock_status='bogus') [error]", query_products(stock_status="bogus"))

    show("calculate_stock_coverage('MZ-SK-001')", calculate_stock_coverage("MZ-SK-001"))
    show("calculate_stock_coverage('MZ-WE-001')  # avg=0 edge", calculate_stock_coverage("MZ-WE-001"))
    show("calculate_stock_coverage('NOPE') [not found]", calculate_stock_coverage("NOPE"))

    show("get_low_stock_items()", get_low_stock_items())
    show("get_low_stock_items(brand='Bomi')", get_low_stock_items(brand="Bomi"))


if __name__ == "__main__":
    _smoke_test()
