from .constants import *

TASK_PROMPT = f"""Analyze customer {TARGET_CUSTOMER_ID}'s Q2 2026 promotional profitability.

Q2 means orders dated {PERIOD_START} through {PERIOD_END}, inclusive. Use only completed orders.
For each completed order, include it only if its returned-quantity rate is no more than 20% of ordered quantity.
For included orders, calculate net revenue from non-returned units after the order discount; do not add shipping to revenue.
Join product unit cost to calculate COGS on the non-returned units. Determine whether the customer earns the applicable
quarterly rebate: the customer's segment and region must have an active policy, and qualifying net revenue must meet
that policy's threshold. Rebate is deducted from contribution margin.

Return ONLY JSON with these keys:
customer_id, included_order_count, qualifying_net_revenue, cogs, rebate_amount,
contribution_margin, contribution_margin_rate, rebate_eligible.
Round money to 2 decimals and rate to 4 decimals. Do not include commentary."""
