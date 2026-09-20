import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config.task import TASK_PROMPT
from environment.api import BusinessEnvironment, BusinessAPIError
from environment.database import build_database
from validator.engine import validate

DB = ROOT / "data" / "business.sqlite"

def main():
    build_database(DB).close()
    env = BusinessEnvironment(DB)
    print("=== Task ===")
    print(TASK_PROMPT)
    print("\n=== Example API interaction ===")
    customer = env.get_customer_profile("C1001")
    orders = env.list_orders("C1001", "2026-04-01", "2026-06-30")
    products = env.get_product_catalog([x["product_id"] for x in orders])
    policy = env.get_rebate_policy(customer["segment"], customer["region"], "2026-06-30")
    print(json.dumps({"customer": customer, "orders": orders, "products": products, "policy": policy}, indent=2))
    correct = json.dumps({
        "customer_id":"C1001","included_order_count":3,"qualifying_net_revenue":15118.10,
        "cogs":9850.00,"rebate_amount":453.54,"contribution_margin":4814.56,
        "contribution_margin_rate":0.3185,"rebate_eligible":True
    })
    wrong = json.dumps({
        "customer_id":"C1001","included_order_count":3,"qualifying_net_revenue":11800,
        "cogs":5000,"rebate_amount":0,"contribution_margin":6800,
        "contribution_margin_rate":0.5763,"rebate_eligible":False
    })
    print("\ncorrect reward:", validate(TASK_PROMPT, correct, str(DB)))
    print("wrong reward:  ", validate(TASK_PROMPT, wrong, str(DB)))
    try:
        env.get_customer_profile("")
    except BusinessAPIError as exc:
        print("handled invalid API input:", exc)
    env.close()

if __name__ == "__main__":
    main()
