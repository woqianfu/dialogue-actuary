# 🧠 对话精算师 | Dialogue Actuary

> **系统级对话 Token 优化守护者** | System-level conversation token optimization guardian for [Hermes Agent](https://hermes-agent.nousresearch.com)

[![Version](https://img.shields.io/badge/version-2.0.0-blue)]()
[![For Hermes Agent](https://img.shields.io/badge/For-Hermes%20Agent-purple)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

## 📋 目录 | Table of Contents

- [这是什么 | What Is This](#-这是什么--what-is-this)
- [核心理念 | Core Philosophy](#-核心理念--core-philosophy)
- [核心亮点 | Key Features](#-核心亮点--key-features)
- [团队架构 | The Team](#-团队架构--the-team)
- [十大原则 | 10 Principles](#-十大原则--10-principles)
- [十一条铁则 | 11 Iron Rules](#-十一条铁则--11-iron-rules)
- [命令参考 | Commands](#-命令参考--commands)
- [技术架构 | Architecture](#-技术架构--architecture)
- [缓存助理深度解析 | Cache Hit Assistant](#-缓存助理深度解析--cache-hit-assistant)
- [真实效果 | Real Impact](#-真实效果--real-impact)
- [安装 | Quick Start](#-安装--quick-start)

---

## 🎯 这是什么 | What Is This

**中文**：对话精算师是 Hermes Agent 的**系统级 Token 消耗优化套件**。它把每个 token 当成钱——指派一个专职"精算师"盯着钱花到了哪里。不是泛泛的省钱建议，而是**真查 DB、真出报表、真告警**。

**English**: Dialogue Actuary is a **system-wide token consumption optimization suite** for Hermes Agent. It treats every token as money — and assigns a dedicated "actuary" to watch where it goes. Not generic cost-saving tips — it **reads real state.db data, produces real reports, and sends real alerts**.

它实际做的事 | What it actually does:
- 📊 **读 state.db** — 不估算，读真实 token 数据
- 🔍 **按来源拆分成本** — TUI / CLI / WeChat / cron / subagent / telegram
- ⚠️ **检测缓存失效** — 系统 prompt 变更时主动告警
- 💰 **追踪月度预算** — 设上限、盯日耗、超额预警
- 👴 **管理 Session 寿命** — >400 条消息或 >$1 成本时提醒翻篇
- 🔧 **分析工具链效率** — 检测死循环、重复读文件、轮均调用

---

## 💡 核心理念 | Core Philosophy

**中文**：Token is money. 每一颗 token 都有成本。精算师不是吝啬，是**精准**——把 token 花在刀刃上，花在真正需要推理和创造力的地方。

**English**: Token is money. Every token has a cost. The Dialogue Actuary is not about being cheap — it's about being **precise**: spending tokens where they create real reasoning and creativity value, and cutting waste everywhere else.

### 缓存现实 | The Cache Reality

```
中文:  缓存率 99% → 每轮 $0.01   |   缓存率 0% → 每轮 $1.50+   |   差距 150 倍
English: 99% cache → $0.01/turn  |   0% cache → $1.50+/turn  |   Difference: 150x
```

---

## ✨ 核心亮点 | Key Features

### 📊 成本覆盖 | Cost Coverage

| 中文 | English |
|------|---------|
| **盲区从 51.6% → 0.0%** | **Blind spot reduced from 51.6% → 0.0%** ✅ |
| WeChat/CLI 之前显示 $0 | WeChat/CLI sessions went from $0 → tracked |
| 自动检测并修复缺失的定价条目 | Auto-detected and filled missing pricing entries |
| 6/6 来源全有成本数据 | All 6 sources now have cost data |

### 🔍 缓存异常检测 | Cache Anomaly Detection

- **中文**: 检测缓存率 <50% 的 session，自动分析根因（新鲜 session / 系统 prompt 变更 / skill 安装）
- **English**: Detects sessions with cache hit rate <50%, auto-analyzes root cause (fresh session / prompt change / skill install)
- **中文**: 30 天内发现 **14 个异常**，标记 **$6.28 潜在浪费**
- **English**: **14 anomalies found in 30 days**, **$6.28 potential waste** flagged
- **中文**: 不遗漏 0% 缓存的严重异常
- **English**: Zero-cache sessions no longer silently ignored

### 🕵️ 缓存杀手扫描 | Cache Killer Scanner

扫描 SKILL.md 和 system prompt，自动检测：

| 杀手 | Killer | 影响 Impact | 发现 Findings |
|------|--------|------------|---------------|
| 🔴 时间戳 | Timestamps | 缓存率 → 0% | 3 个 skill 文件 |
| 🟡 JSON key 未固定排序 | Missing sort_keys | 相同数据不同哈希 | 7+ 个 skill |
| 🟡 用户标识放错位置 | User ID at wrong position | 每个用户独占前缀 | 8+ 个 skill |
| 🟢 随意改 prompt | Casual prompt edits | 整个缓存清空 | 常见习惯 |

### 👴 Session 寿命管理 | Session Lifecycle

- **中文**: 870 条消息的 session 花 $4.91，617 条的同样任务花 $0.41 — **差 12 倍**
- **English**: 870-message session cost $4.91 vs 617-message at $0.41 — **12x difference**
- **中文**: >400 条消息或 >$1 成本时主动提醒翻篇
- **English**: Auto-alerts when session exceeds 400 messages or $1.00 cost

### 💰 月度预算 | Monthly Budget

- **中文**: 设月度上限、按日跟踪、预测月底总额、超额 🔴 告警
- **English**: Set monthly cap, track daily burn, project month-end, 🔴 overspend alert
- **中文**: 自动发现本月超预算 **156%**（$10 预算实花 $25.59）
- **English**: Auto-discovered **156% budget overspend** ($10 budget, $25.59 actual)

### 🔧 工具链优化 | Toolchain Optimization

- **中文**: 轮均调用 >5 次提示合并；检测死循环（同一工具失败 3 次+）；标记重复读文件
- **English**: Alerts on >5 tools/round; detects retry loops (same tool failing 3x+); flags repeated file reads
- **中文**: 每工具调用 ~80 token，5 次合并 = 省 320+ token
- **English**: Each tool call ~80 tokens, merging 5 saves 320+

### 📈 趋势与峰值复盘 | Trends & Peak Review

- **中文**: 每日自动记录趋势、7 天/14 天视图
- **English**: Daily auto-trending, 7-day / 14-day views
- **中文**: 自动分析 Top-3 最贵日及其根因
- **English**: Auto-analysis of Top-3 most expensive days with root cause

---

## 👥 团队架构 | The Team

精算师不是一个人，是一个 **6 人团队**：

```
对话精算师（总会计师 | General Accountant）
│
├── 🎯 缓存命中助理    Cache Hit Assistant    → cache-hit-assistant
│    ├ 缓存健康报告 · 缓存杀手检测 · 重建成本预警
│    ├ Cache health reports · killer detection · rebuild warnings
│    └ 3 scripts + 1 reference
│
├── ✂️ 输出精算师      Output Actuary         → output-actuary
│    ├ 输出/输入比 · 话痨检测
│    ├ Output/input ratio · verbose session ranking
│    └ scripts/output-efficiency.py
│
├── 👴 Session 寿命管理员  Session Lifecycle Manager → session-lifecycle-manager
│    ├ session 翻篇 · subagent 追踪 · 继承链
│    ├ Session age · subagent tracking · inheritance chain
│    └ scripts/session-age-check.py
│
├── 💰 预算管家         Budget Manager         → budget-manager
│    ├ 月度预算 · 超额预警
│    ├ Monthly budget · overspend alerts
│    └ scripts/budget-status.py
│
└── 🔧 工具链优化师     Toolchain Optimizer    → toolchain-optimizer
     ├ 调用密度 · 死循环 · 合并建议
     ├ Tool density · retry detection · merge suggestions
     └ scripts/toolchain-stats.py
```

每个助理是一个**独立的 Hermes Skill**，可单独加载。共同提供全覆盖。

---

## 📐 十大原则 | 10 Principles

| # | 中文 | English | 省多少 |
|---|------|---------|--------|
| P1 | **输入信噪比** — 精确路径 > 模糊搜索 | **Input SNR** — precise paths over fuzzy search | 500-3000 tok/次 |
| P2 | **输出压缩** — 不寒暄不讲废话 | **Output compression** — no chit-chat | 40-60% |
| P3 | **上下文管理** — 按需加载 skill | **Context management** — load skills on demand | 数千/次 |
| P4 | **任务分级** — L1 ≤100 字, L4 不限 | **Task grading** — match effort to need | 按需 |
| P5 | **决策断舍离** — 本地工具 > LLM | **Decision triage** — local tool > LLM | 防浪费 |
| P6 | **CLI 压缩** — RTK + Caveman 引擎 | **CLI compression** — RTK + Caveman engine | 88-92% |
| P7 | **协议级优化** — 缓存率是命 | **Protocol optimization** — cache rate is sacred | 96-99% |
| P8 | **预算与趋势** — 月上限、日告警 | **Budget & trends** — monthly cap, daily alert | 防超支 |
| P9 | **缓存失效防护** — 批量操作、事前预警 | **Cache invalidation guard** — batch, warn first | $1.50+/次 |
| P10 | **会话生命周期** — 400 条消息/$1 翻篇 | **Session lifecycle** — turn the page | 防 12x |

---

## ⚡ 十一条铁则 | 11 Iron Rules

| # | 中文 | English | 代价 Cost |
|---|------|---------|-----------|
| 1 | **完整性 > 节省** | Integrity > Savings | 用户不信任 |
| 2 | **直球回答** | Direct answers | 100-500 tok/轮 |
| 3 | **结构化优先** | Structured output | 省 40-60% |
| 4 | **精准引用** | Precise references | 省 500-3000 |
| 5 | **记忆优先** | Memory first | 省 500+ |
| 6 | **压缩终端输出** | Compress terminal | 省 88-92% |
| 7 | **批量操作** | Batch operations | 省 80+/工具 |
| 8 | **不主动报告** | Don't report proactively | 汇报花 token |
| 9 | **快速失败** | Fail fast | 防死循环 |
| 10 | **缓存失效警惕** | Cache breach alert | $1.50+/次 |
| 11 | **会话翻篇** | Session turnover | 12x 退化 |

---

## 📖 命令参考 | Commands

### 精算师核心 | Core Actuary

| 你说 (Chinese) | You Say (English) | 执行 (Executes) |
|---------------|-------------------|-----------------|
| "查今日" / "今天花了" | "today's spending" | `--today` |
| "统计全部" / "总花费" | "total cost" | `--all` |
| "查成本来源" | "cost coverage" | `--coverage` |
| "查零缓存" | "zero cache" | `--zero-cache` |
| "查趋势" / "最近趋势" | "trend" | `--view` |
| "精算审计" / "全面审计" | "full audit" | `--audit` |
| "峰值复盘" | "peak review" | `--peak` |
| "按 skill 归因" | "skill ROI" | `skill-roi-analyzer.py` |
| "查 session 老化" | "session aging" | `--aging` |
| "本月预算 $X" | "set budget $X" | Budget tracking |

### 缓存助理 | Cache Hit Assistant

| 你说 | You Say | 执行 |
|------|---------|------|
| "缓存状态" | "cache status" | `cache-health-check.py` |
| "查缓存异常" | "cache anomalies" | `cache-anomaly-detector.py` |
| "查缓存杀手" | "cache killers" | `cache-killer-detector.py` |
| "这个操作烧缓存吗" | "will this burn cache?" | `cache-rebuild-warner.py` |

### 其他助理 | Other Specialists

| 助理 Specialist | 中文命令 | English Command |
|----------------|---------|-----------------|
| 输出精算师 Output Actuary | "输出效率" | "output efficiency" |
| 寿命管理员 Session Manager | "会话年龄" | "session age" |
| 预算管家 Budget Manager | "预算状态" | "budget status" |
| 工具链优化师 Toolchain Optimizer | "工具效率" | "tool efficiency" |

---

## 🏗 技术架构 | Architecture

```
Hermes state.db (SQLite)
│
├── sessions 表
│   ├── input_tokens, output_tokens        ← 原始 token 计数
│   ├── cache_read_tokens, cache_write     ← 缓存性能
│   ├── estimated_cost_usd, actual_cost    ← 成本数据
│   ├── model, billing_provider            ← 定价上下文
│   ├── source (tui/cli/weixin/cron/subagent)
│   ├── parent_session_id                  ← 继承链
│   └── system_prompt                      ← skill 归因
│
└── messages 表
    ├── tool_name, tool_calls              ← 工具链分析
    └── finish_reason, timestamp
                    │
                    ▼
    ┌──────────────────────────────────────────┐
    │        精算师核心脚本 Core Scripts         │
    │                                          │
    │  token-usage-estimator.py   ← 成本查询   │
    │  token-trend-tracker.py     ← 每日趋势   │
    │  cache-anomaly-detector.py  ← 缓存健康   │
    │  session-cost-monitor.py    ← 老化+审计  │
    │  skill-roi-analyzer.py      ← skill ROI │
    │  token_utils.py             ← 共享模块   │
    └──────────────────────────────────────────┘
```

**共享工具层 Shared Utility** — `token_utils.py`:
- `resolve_db()` — 统一 profile 感知的 DB 路径
- `safe_connect()` — 安全连接，不崩溃
- `fmt_num()` / `fmt_time()` — 统一格式化
- 定价常量 — `$0.14/M 输入` `$0.28/M 输出` `$0.003/M 缓存读`
- `cache_rate()` — 缓存率计算，防除零

---

## 🎯 缓存助理深度解析 | Cache Hit Assistant Deep Dive

### 检测能力 | Detection Capabilities

| 检测项 Detection | 方法 Method | 结果 Result |
|-----------------|------------|-------------|
| 零缓存 session | SQL `cache_read_tokens=0` | **6 个发现**，$9.28 浪费 |
| 低缓存 session | 比例检查 <50% | **14 个异常/30天** |
| SKILL.md 中缓存杀手 | 扫描 120+ 个 skill 文件 | **5 个时间戳发现** |
| 缓存重建成本 | 当前缓存 × 定价 | **~$17.85 重建税** |
| 每日趋势对比 | 昨日 vs 今日缓存率 | **1.8pp 下降检测** |

### 缓存重建预警 | Rebuild Warning

```
⚠️ 当前缓存: 31.5M tokens (~$0.15)
   首轮重建成本: $4.46
   恢复到 90%+ 缓存率: $13.39 (~3轮)
   总缓存税: ~$17.85
   建议: 一次性完成所有安装/变更，别拆成多次
```

### 发现的真实缓存杀手 | Real Killers Found

| 文件 File | 问题 Issue |
|-----------|-----------|
| `hermes-operations/SKILL.md` | 动态时间戳 |
| `open-webui-setup/SKILL.md` | 时间相关内容 |
| `google-workspace/scripts/` | `datetime.now()` 在工具集成中 |
| 7+ 个 skill | `json.dumps` 缺少 `sort_keys=True` |
| 8+ 个 skill | 用户 ID 引用在系统 prompt 中 |

---

## 📊 真实效果 | Real Impact

### 成本覆盖 | Cost Coverage

| 指标 Metric | 之前 Before | 之后 After |
|-------------|------------|-----------|
| 成本盲区 Blind spot | **51.6%** | **0.0%** ✅ |
| DeepSeek-v4-flash 成本 | **$0** (185 sessions) | **$2.83** |
| WeChat 成本可见性 | **$0** | **$0.95** |
| CLI 成本可见性 | **$0** | **$0.12** |
| 已跟踪来源 Sources tracked | 2/6 | **6/6** |

### 发现的节省机会 | Savings Discovered

| 发现 Finding | 金额 Amount | 根因 Root Cause |
|-------------|------------|-----------------|
| Skill 安装缓存失效 | **$14.17 (71%)** | 8 次安装尝试 |
| Subagent 零缓存开销 | **$4.51 (22.5%)** | 21 个 subagent |
| Session 年龄退化 | **12x 成本** | 870 条 vs 617 条 |
| 预算超支 | **156%** | $10 预算, 实花 $25.59 |

---

## 🚀 安装 | Quick Start

### 前置条件 | Prerequisites

- [Hermes Agent](https://hermes-agent.nousresearch.com) installed

### 安装 | Install

```bash
# 安装精算师核心
hermes skills install hermes-token-saver

# （可选）安装专职助理 | (Optional) Install specialists
hermes skills install cache-hit-assistant
hermes skills install output-actuary
hermes skills install session-lifecycle-manager
hermes skills install budget-manager
hermes skills install toolchain-optimizer
```

### 首次运行 | First Run

```bash
# 查看成本覆盖
cd ~/.hermes/skills/hermes/hermes-token-saver
python3 scripts/token-usage-estimator.py --coverage

# 查看今日花费
python3 scripts/token-usage-estimator.py --today

# 运行全面审计
python3 scripts/session-cost-monitor.py --audit
```

### 每日自动报告 | Daily Auto-Report

23:59 每天自动运行审计，生成费用清单。

手动注册 cron：
```bash
hermes cron create \
  --name "每日Token费用清单" \
  --schedule "59 23 * * *" \
  --prompt "生成每日 Token 消耗与费用清单"
```

---

## 🔄 自检机制 | Self-Check

精算师定期进行 **10 轮深度自检**，每轮执行 3 项任务：① 逻辑校验 ② 完善优化 ③ 发散创新。

### v1.3 → v2.0 审计日志 | Audit Log

| 轮次 | 盲区 Blind Spot | 发现 Discovery | 新增 Added |
|------|----------------|---------------|-----------|
| D1 | Skill 安装缓存失效 | 8 次安装 = $14.17 (71%) | P9 原则 |
| D2 | Subagent 零缓存 | 21 个 = $4.51 (22.5%) | P10 原则 |
| D3 | WeChat/CLI 成本盲区 | 2.3M token 无成本 | `--coverage` |
| D4 | 零缓存无告警 | 6 个 session, $9.28 | `cache-anomaly-detector.py` |
| D5 | Session 年龄退化 | 12x 成本差 | `--aging` |
| D6 | 跨 profile 盲区 | 仅 default 被追踪 | `--cross-profile` |
| D7 | 峰值无自动复盘 | $15.90 事后才知 | `--peak` |
| D8 | 任务意图归因缺失 | 全部 subagent title="?" | 标签规范建议 |

### 当前版本 | Current Version

**v2.0.0** — [CHANGELOG](https://github.com/woqianfu/dialogue-actuary/releases)

---

## 📄 许可 | License

MIT

---

## 🙏 致谢 | Acknowledgments

- **Hermes Agent** ([Nous Research](https://nousresearch.com)) — 本 Skill 所扩展的 Agent 框架
- **RTK + Caveman** — CLI 输出压缩技术 (88-92% 节省)
- **DeepSeek API Docs** — KV 缓存机制文档
- **KV-Cache Aware Prompt Engineering** — 65% 延迟改进启发
- **Prompt Cache Hit Rate** (Tian Pan) — 生产环境缓存率监控框架

---

<p align="center">
  <i>Token is money. Spend it precisely.</i><br>
  <i>Token 就是钱。花准点。</i>
</p>
