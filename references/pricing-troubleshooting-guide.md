# Hermes 成本追踪诊断与修复

> 精算师 v2.0 实测方法，用于诊断和修复 Hermes 成本覆盖盲区。

## 诊断工作流

### 1. 检测盲区

```bash
# 精算师覆盖检测
python3 scripts/token-usage-estimator.py --coverage

# 查看具体哪些 session 成本为 0
sqlite3 ~/.hermes/state.db "
SELECT source, model, cost_source, COUNT(*) as sessions,
       SUM(input_tokens) as inp, SUM(output_tokens) as out,
       SUM(cache_read_tokens) as cache
FROM sessions
WHERE (estimated_cost_usd IS NULL OR estimated_cost_usd = 0)
  AND (input_tokens > 0 OR output_tokens > 0)
GROUP BY source, model, cost_source
ORDER BY sessions DESC;
"
```

### 2. 定位缺失来源

```bash
# 查看 cost_source 分布
sqlite3 ~/.hermes/state.db "SELECT DISTINCT cost_source, COUNT(*) FROM sessions GROUP BY cost_source;"

# 查看哪些有成本、哪些没有
sqlite3 ~/.hermes/state.db "
SELECT model, billing_provider,
       SUM(estimated_cost_usd) as total_cost,
       SUM(input_tokens) as inp, SUM(output_tokens) as out,
       SUM(cache_read_tokens) as cache, COUNT(*) as sessions
FROM sessions WHERE estimated_cost_usd > 0 AND model IS NOT NULL
GROUP BY model, billing_provider ORDER BY total_cost DESC;
"
```

### 3. 定位定价表缺失

Hermes 定价表在 `agent/usage_pricing.py` 的 `_OFFICIAL_DOCS_PRICING` 字典。

```bash
grep -A 10 '"deepseek".*"模型名"' agent/usage_pricing.py
grep -B 2 -A 8 '"deepseek-chat"' agent/usage_pricing.py  # 检查缺 cache_read?
```

### 4. 修复

在 `_OFFICIAL_DOCS_PRICING` 中添加条目或补全缺失字段。

```
("provider", "model"): PricingEntry(
    input_cost_per_million=Decimal("X.XX"),
    output_cost_per_million=Decimal("X.XX"),
    cache_read_cost_per_million=Decimal("X.XX"),
    source="official_docs_snapshot",
    source_url="https://...",
    pricing_version="provider-pricing-YYYY-MM-DD",
),
```

### 5. 回填历史数据

对已写入 DB 的 session 执行 UPDATE 回填成本。详见 v2.0 审计中的 `deepseek-v4-flash` 修复示例。

### 6. 验证

```bash
python3 scripts/token-usage-estimator.py --coverage
```
盲区应为 0.0%。

## DeepSeek 族定价（实测）

| 模型 | 输入 $/M | 输出 $/M | 缓存读 $/M | 备注 |
|------|---------|---------|-----------|------|
| `deepseek-chat` | 0.14 | 0.28 | 0.003 | v2.0 修复前缺 cache_read |
| `deepseek-reasoner` | 0.55 | 2.19 | — | |
| `deepseek-v4-pro` | 1.74 | 3.48 | 0.0145 | |
| `deepseek-v4-flash` | 0.14 | 0.28 | 0.003 | v2.0 新增 |
| `deepseek/deepseek-chat` | 0.14 | 0.28 | 0.003 | 路由别名 |

## 深层追踪：Pricing Entry 调用链

如果 `--coverage` 仍然有盲区，按以下链路追踪：

```python
# 每步调用链
conversation_loop.py:1833 → estimate_usage_cost()
  → usage_pricing.py:784 → resolve_billing_route()
  → usage_pricing.py:794 → get_pricing_entry(model, provider, base_url)
    → 如果有 base_url:
        → _pricing_entry_from_metadata(fetch_endpoint_model_metadata(), model)
        → 如果返回 None:
           → _lookup_official_docs_pricing(route)
             → _OFFICIAL_DOCS_PRICING.get((provider, model))
             → 如果 None → 返回 None
           → if not entry: return CostResult(None, "unknown", "none")
```

### 关键断点检查

```bash
python3 -c "
import sys; sys.path.insert(0, '$HOME/.hermes/hermes-agent')
from agent.usage_pricing import resolve_billing_route, get_pricing_entry
route = resolve_billing_route('deepseek-v4-flash', provider='deepseek')
print(f'Route: provider={route.provider}, billing_mode={route.billing_mode}')
entry = get_pricing_entry('deepseek-v4-flash', provider='deepseek')
if entry:
    print(f'✅ 找到: input={entry.input_cost_per_million}')
else:
    print('❌ 未找到')
"
```

## 常见脚本级 Bug 模式

本会话修复过程中发现多个跨脚本的重复 bug 模式：

| 模式 | 修复 | 涉及文件 |
|------|------|---------|
| `source='tui'` 硬编码过滤 | 移除或改为 `source IN (...)`, 输出分组 | `session-cost-monitor.py` |
| 总成本 `cost_est + cost_act` 双重计数 | 改用 `cost_est or cost_act or 0` | `session-cost-monitor.py` |
| UTC 零点偏移（本地早 8 点数据丢失） | 用 `datetime.now()` 本地时间 | `cache-health-check.py` |
| 活跃天计数 → 固定窗口天 | `len(recent_days)` → `day_count=7` | `token-usage-estimator.py` |
| 轮均分母错用 `message_count` | 应为 `message_count - tool_call_count` | `toolchain-stats.py` |
| 输出成本错用输入费率 | $0.14/M → $0.28/M | `toolchain-stats.py` |
