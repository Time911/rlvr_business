<<<<<<< HEAD
# rlvr_business
=======
# API-Driven Multi-Step Business Analysis RLVR Task

一个可直接接入 RLVR Training Harness 的单场景任务：**企业客户季度促销利润归因**。

## 1. 任务目标

Agent 只允许通过业务 API 获取环境信息，完成 C1001 在 2026 Q2 的促销利润分析。任务要求 Agent：

1. 查询客户画像，推导适用的客户分群与区域政策；
2. 查询 Q2 订单，识别 completed 订单并计算退货率；
3. 根据订单中的 product_id 查询商品成本；
4. 查询返利政策；
5. 进行跨 API 关联与二次计算，得到净收入、COGS、返利、贡献利润和利润率。

环境额外提供 `get_inventory_snapshot` 冗余 API，返回结果对本任务无用，用于测试 Agent 的工具选择能力。

## 2. 为什么不是单步任务

任何单个 API 都无法得到最终答案：客户 API 不含订单，订单 API 不含商品成本，商品 API 不含客户政策，政策 API 也不含实际收入。最终答案必须完成跨表 join、退货率过滤、折扣计算、成本计算、返利资格判断及利润二次计算。

隐含约束包括：Q2 是日期区间而不是字符串关键词；只有 `COMPLETED` 订单有效；单笔订单退货率必须 `<= 20%`；返利需要同时满足客户 segment/region 政策匹配与净收入门槛。

## 3. API

Python 类 `environment.api.BusinessEnvironment` 提供：

```python
get_customer_profile(customer_id)
list_orders(customer_id, start_date, end_date)
get_product_catalog(product_ids)
get_rebate_policy(segment, region, as_of_date)
get_inventory_snapshot(product_id)  # redundant
```

Agent 不获得 SQLite connection，也不能直接访问数据库。

## 4. Validator

入口：

```python
from validator.engine import validate
reward = validate(task_prompt, agent_output, db_path)
```

输出严格位于 `[0, 1]`。验证器只比较最终 JSON 与环境根据真实业务规则重算出的答案，不检查 API 次数、顺序或轨迹。

字段级 reward 权重：customer 0.10、order count 0.10、revenue 0.20、COGS 0.20、rebate 0.10、margin 0.15、margin rate 0.10、rebate eligibility 0.05。

核心验证完全使用 Python 标准库 + SQLite + Decimal，无大模型调用。

## 5. Expected result

正确答案：

```json
{"customer_id":"C1001","included_order_count":3,"qualifying_net_revenue":15118.10,"cogs":9850.00,"rebate_amount":453.54,"contribution_margin":4814.56,"contribution_margin_rate":0.3185,"rebate_eligible":true}
```

## 6. Local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python examples/run_demo.py
pytest -q
```

## 7. Docker

```bash
docker build -t api-driven-rlvr-task .
docker run --rm api-driven-rlvr-task
```

容器启动会初始化内置 SQLite 数据，并执行一个正确结果和一个错误结果场景。

## 8. Harness integration

训练框架可以把 `TASK_PROMPT` 发给 Agent，将 Agent 最终文本传入 `validate()`：

```python
from config.task import TASK_PROMPT
from validator.engine import validate

reward = validate(TASK_PROMPT, agent_final_output, "/path/to/business.sqlite")
```

Harness 自己负责 trajectory / tool-call 记录；本项目不把轨迹作为 reward 输入，因此符合“结果正确性是唯一核心判定依据”的要求。

## 9. One-function Harness facade

`rlvr_task.py` 提供最小集成面：

```python
from rlvr_task import initialize, get_task

db_path = initialize("./data")
task = get_task(db_path)
# task["prompt"] -> 发给 Agent
# task["environment_factory"]() -> 创建业务 API 环境
# task["validator"](agent_output) -> 取得 0~1 reward
```

这样训练 Harness 不需要了解数据库 schema，也不需要依赖验证器内部实现。
>>>>>>> 1c833d6 (Initial commit)
