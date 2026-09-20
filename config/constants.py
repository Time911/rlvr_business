from decimal import Decimal

TASK_ID = "enterprise_promo_margin_v1"
TARGET_CUSTOMER_ID = "C1001"
PERIOD_START = "2026-04-01"
PERIOD_END = "2026-06-30"

# Hidden business rules that must be inferred from the task wording/data.
VALID_ORDER_STATUSES = ("COMPLETED",)
MAX_RETURN_RATE_FOR_INCLUDED_ORDER = Decimal("0.20")
MIN_NET_REVENUE_FOR_REBATE = Decimal("10000.00")
ELIGIBLE_CUSTOMER_SEGMENTS = ("GOLD", "PLATINUM")
REBATE_RATE = Decimal("0.03")
MARGIN_WARNING_THRESHOLD = Decimal("0.10")

# Scoring tolerances.
MONEY_TOLERANCE = Decimal("0.01")
RATE_TOLERANCE = Decimal("0.0001")
COUNT_TOLERANCE = 0
