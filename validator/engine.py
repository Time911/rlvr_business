from __future__ import annotations
import json
import re
import sqlite3
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any
from config.constants import *

MONEY_FIELDS = ("qualifying_net_revenue", "cogs", "rebate_amount", "contribution_margin")
RATE_FIELDS = ("contribution_margin_rate",)
REQUIRED_FIELDS = ("customer_id", "included_order_count", *MONEY_FIELDS, *RATE_FIELDS, "rebate_eligible")

class ValidationError(Exception):
    pass

def _money(x: Any) -> Decimal:
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def _rate(x: Any) -> Decimal:
    return Decimal(str(x)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

def _parse_json(text: str) -> dict[str, Any] | None:
    if not isinstance(text, str):
        return None
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        # Permit a single fenced JSON object without allowing arbitrary prose extraction.
        m = re.fullmatch(r"\s*```(?:json)?\s*(\{.*\})\s*```\s*", text, re.S)
        if not m:
            return None
        try:
            value = json.loads(m.group(1))
        except json.JSONDecodeError:
            return None
    return value if isinstance(value, dict) else None

def _expected(conn: sqlite3.Connection) -> dict[str, Any]:
    customer = conn.execute("SELECT * FROM customers WHERE customer_id=?", (TARGET_CUSTOMER_ID,)).fetchone()
    orders = conn.execute(
        "SELECT * FROM orders WHERE customer_id=? AND order_date BETWEEN ? AND ?",
        (TARGET_CUSTOMER_ID, PERIOD_START, PERIOD_END),
    ).fetchall()
    included = []
    for o in orders:
        if o["status"] != "COMPLETED":
            continue
        return_rate = Decimal(o["returned_quantity"]) / Decimal(o["quantity"])
        if return_rate <= MAX_RETURN_RATE_FOR_INCLUDED_ORDER:
            included.append(o)
    product_ids = [o["product_id"] for o in included]
    products = {}
    if product_ids:
        qs = ",".join("?" * len(set(product_ids)))
        rows = conn.execute(f"SELECT * FROM products WHERE product_id IN ({qs})", tuple(dict.fromkeys(product_ids))).fetchall()
        products = {r["product_id"]: r for r in rows}
    revenue = Decimal("0")
    cogs = Decimal("0")
    for o in included:
        sold = Decimal(o["quantity"] - o["returned_quantity"])
        revenue += sold * Decimal(str(o["unit_price"])) * (Decimal("1") - Decimal(str(o["discount_rate"])))
        cogs += sold * Decimal(str(products[o["product_id"]]["unit_cost"]))
    policy = conn.execute(
        "SELECT * FROM rebate_policies WHERE segment=? AND region=? AND effective_from<=? AND effective_to>=?",
        (customer["segment"], customer["region"], PERIOD_END, PERIOD_END),
    ).fetchone()
    eligible = bool(policy and customer["segment"] in ELIGIBLE_CUSTOMER_SEGMENTS and revenue >= Decimal(str(policy["min_net_revenue"])))
    rebate = revenue * Decimal(str(policy["rebate_rate"])) if eligible else Decimal("0")
    margin = revenue - cogs - rebate
    rate = margin / revenue if revenue else Decimal("0")
    return {
        "customer_id": TARGET_CUSTOMER_ID,
        "included_order_count": len(included),
        "qualifying_net_revenue": _money(revenue),
        "cogs": _money(cogs),
        "rebate_amount": _money(rebate),
        "contribution_margin": _money(margin),
        "contribution_margin_rate": _rate(rate),
        "rebate_eligible": eligible,
    }

def validate(task: str, agent_output: str, db_path: str) -> float:
    """Return objective reward in [0, 1]. The task text is accepted for Harness compatibility."""
    try:
        actual = _parse_json(agent_output)
        if actual is None or set(actual.keys()) != set(REQUIRED_FIELDS):
            return 0.0
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        expected = _expected(conn)
        conn.close()
        score = 0.0
        weights = {
            "customer_id": 0.10, "included_order_count": 0.10,
            "qualifying_net_revenue": 0.20, "cogs": 0.20,
            "rebate_amount": 0.10, "contribution_margin": 0.15,
            "contribution_margin_rate": 0.10, "rebate_eligible": 0.05,
        }
        for field, weight in weights.items():
            try:
                if field in MONEY_FIELDS:
                    ok = abs(_money(actual[field]) - expected[field]) <= MONEY_TOLERANCE
                elif field in RATE_FIELDS:
                    ok = abs(_rate(actual[field]) - expected[field]) <= RATE_TOLERANCE
                elif field == "included_order_count":
                    ok = int(actual[field]) == expected[field]
                elif field == "rebate_eligible":
                    ok = isinstance(actual[field], bool) and actual[field] == expected[field]
                else:
                    ok = actual[field] == expected[field]
            except (ValueError, TypeError, InvalidOperation):
                ok = False
            score += weight if ok else 0.0
        return round(min(1.0, max(0.0, score)), 6)
    except (sqlite3.Error, OSError):
        return 0.0
