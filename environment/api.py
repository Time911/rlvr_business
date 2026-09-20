from __future__ import annotations
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

class BusinessAPIError(Exception):
    pass

class BusinessEnvironment:
    """Only business APIs are exposed; callers never receive the DB connection."""
    def __init__(self, db_path: str | Path):
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row

    def _date(self, value: str) -> str:
        try:
            return date.fromisoformat(value).isoformat()
        except (TypeError, ValueError) as exc:
            raise BusinessAPIError(f"invalid date: {value}") from exc

    def get_customer_profile(self, customer_id: str) -> dict[str, Any]:
        if not isinstance(customer_id, str) or not customer_id:
            raise BusinessAPIError("customer_id must be a non-empty string")
        row = self._conn.execute("SELECT * FROM customers WHERE customer_id=?", (customer_id,)).fetchone()
        if row is None:
            raise BusinessAPIError(f"customer not found: {customer_id}")
        return dict(row)

    def list_orders(self, customer_id: str, start_date: str, end_date: str) -> list[dict[str, Any]]:
        start, end = self._date(start_date), self._date(end_date)
        if start > end:
            raise BusinessAPIError("start_date must be <= end_date")
        rows = self._conn.execute(
            """SELECT order_id, customer_id, order_date, status, product_id, quantity,
                      unit_price, discount_rate, returned_quantity, shipping_fee
               FROM orders WHERE customer_id=? AND order_date BETWEEN ? AND ?
               ORDER BY order_date, order_id""",
            (customer_id, start, end),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_product_catalog(self, product_ids: list[str]) -> list[dict[str, Any]]:
        if not isinstance(product_ids, list) or not product_ids or any(not isinstance(x, str) for x in product_ids):
            raise BusinessAPIError("product_ids must be a non-empty list of strings")
        unique = list(dict.fromkeys(product_ids))
        placeholders = ",".join("?" for _ in unique)
        rows = self._conn.execute(f"SELECT * FROM products WHERE product_id IN ({placeholders})", unique).fetchall()
        return [dict(r) for r in rows]

    def get_rebate_policy(self, segment: str, region: str, as_of_date: str) -> dict[str, Any] | None:
        as_of = self._date(as_of_date)
        row = self._conn.execute(
            """SELECT * FROM rebate_policies
               WHERE segment=? AND region=? AND effective_from<=? AND effective_to>=?""",
            (segment, region, as_of, as_of),
        ).fetchone()
        return dict(row) if row else None

    def get_inventory_snapshot(self, product_id: str) -> dict[str, Any]:
        # Deliberately redundant API: valid tool but irrelevant to this task.
        row = self._conn.execute("SELECT product_id, product_name, supplier_tier FROM products WHERE product_id=?", (product_id,)).fetchone()
        if row is None:
            raise BusinessAPIError(f"product not found: {product_id}")
        return {**dict(row), "available_units": 999}

    def close(self) -> None:
        self._conn.close()
