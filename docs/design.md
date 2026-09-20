# Design Note

## 场景

企业销售部门需要判断一个重点客户在季度促销活动中的真实贡献利润。Agent 必须从分散业务 API 获取事实，再根据隐含规则进行分析。

## 典型路径

A. `get_customer_profile(C1001)` -> GOLD / EAST。

B. `list_orders(C1001, 2026-04-01, 2026-06-30)` -> 5 条 Q2 订单，其中包含取消订单以及高退货率订单。Agent 必须识别这些不是最终核算对象。

C. 从保留下来的订单提取 product_id，调用 `get_product_catalog([...])` -> 获取单位成本。

D. 用客户 segment + region + Q2 截止日调用 `get_rebate_policy(...)` -> 得到返利门槛与比例。

E. 计算：

- sold_units = quantity - returned_quantity
- net_revenue = sold_units × unit_price × (1 - discount_rate)
- COGS = sold_units × unit_cost
- rebate = net_revenue × rebate_rate（仅在政策有效且达到门槛时）
- contribution_margin = net_revenue - COGS - rebate
- margin_rate = contribution_margin / net_revenue

## 挑战点

- 多 API join；
- 日期区间语义；
- 状态过滤；
- 退货率阈值判断；
- 非必要 shipping 字段不能被错误计入 revenue；
- 返利需要同时满足政策匹配和收入门槛；
- 冗余库存 API诱导错误工具调用；
- 最终必须输出固定 JSON，便于无模型验证。

## Reward 设计

采用字段级部分奖励而非 all-or-nothing。这样可以区分“客户识别正确但计算错误”和“完全错误”的轨迹，同时避免验证器需要理解自然语言推理过程。金额使用 Decimal 并允许 0.01 的误差，利润率允许 0.0001 的误差。

## 安全与可复现性

数据库由固定 seed 数据脚本创建，任务规则与阈值集中在 `config/constants.py`。Validator 独立于 Environment 的 API 调用记录，避免把工具调用策略错误地编码进 reward。
