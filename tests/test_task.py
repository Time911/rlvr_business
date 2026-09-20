import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from environment.database import build_database
from environment.api import BusinessEnvironment, BusinessAPIError
from config.task import TASK_PROMPT
from validator.engine import validate

DB = Path(__file__).resolve().parents[1] / "data" / "test.sqlite"

def setup_module():
    build_database(DB).close()

def test_api_surface_and_invalid_input():
    env = BusinessEnvironment(DB)
    assert env.get_customer_profile("C1001")["segment"] == "GOLD"
    orders = env.list_orders("C1001", "2026-04-01", "2026-06-30")
    assert len(orders) == 5
    assert len(env.get_product_catalog([o["product_id"] for o in orders])) == 5
    assert env.get_rebate_policy("GOLD", "EAST", "2026-06-30")["rebate_rate"] == 0.03
    try:
        env.list_orders("C1001", "bad", "2026-06-30")
        assert False
    except BusinessAPIError:
        pass
    env.close()

def test_rewards():
    correct = json.dumps({"customer_id":"C1001","included_order_count":3,"qualifying_net_revenue":15118.10,"cogs":9850.00,"rebate_amount":453.54,"contribution_margin":4814.56,"contribution_margin_rate":0.3185,"rebate_eligible":True})
    wrong = json.dumps({"customer_id":"C1001","included_order_count":3,"qualifying_net_revenue":11800,"cogs":5000,"rebate_amount":0,"contribution_margin":6800,"contribution_margin_rate":0.5763,"rebate_eligible":False})
    assert validate(TASK_PROMPT, correct, str(DB)) == 1.0
    assert 0.0 < validate(TASK_PROMPT, wrong, str(DB)) < 1.0
    assert validate(TASK_PROMPT, "not json", str(DB)) == 0.0
