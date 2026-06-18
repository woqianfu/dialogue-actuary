# Dialogue Actuary — Token Cost Optimization & Cache Hit Guardian for Hermes Agent

> **对话精算师** — 系统级对话 Token 优化守护者 | System-level conversation token optimization guardian

[![Version](https://img.shields.io/badge/version-2.0.0-blue)]()
[![Hermes Agent](https://img.shields.io/badge/For-Hermes%20Agent-purple)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

---

## 📋 Table of Contents

- [What Is This](#-what-is-this)
- [Core Philosophy](#-core-philosophy)
- [Key Features — Highlights](#-key-features--highlights)
- [The Team: 1 General + 5 Specialists](#-the-team-1-general--5-specialists)
- [10 Principles of Token Optimization](#-10-principles-of-token-optimization)
- [11 Iron Rules](#-11-iron-rules)
- [Technical Architecture](#-technical-architecture)
- [Cache Hit Assistant Deep Dive](#-cache-hit-assistant-deep-dive)
- [Real-World Impact](#-real-world-impact)
- [Quick Start](#-quick-start)
- [Commands Reference](#-commands-reference)
- [Development & Self-Check](#-development--self-check)
- [License](#-license)

---

## 🎯 What Is This

Dialogue Actuary is a **system-wide token consumption optimization suite** for [Hermes Agent](https://hermes-agent.nousresearch.com). It treats every token as money — and assigns a dedicated "actuary" to watch where it goes.

Unlike generic cost-saving tips, Dialogue Actuary actually:
1. **Reads Hermes' `state.db`** — real token usage data, not estimates
2. **Reports per-source cost breakdown** (TUI, CLI, WeChat, cron, subagent)
3. **Detects cache invalidation events** — the #1 cost driver in LLM conversations
4. **Tracks budget vs. actual** — sets monthly caps and alerts on overspend
5. **Monitors session aging** — long sessions degrade to 12x cost
6. **Analyzes tool call efficiency** — detects retry loops, redundant reads
7. **Audits daily at 23:59** — automated full-system cost report

All **fully automated** — no manual configuration needed. Install the skill and it starts working.

---

## 💡 Core Philosophy

> **Token is money.** Every token has a cost. The Dialogue Actuary is not about being cheap — it's about being **precise**: spending tokens where they create real reasoning and creativity value, and cutting waste everywhere else.

### The Cache Reality

```
With 99% cache hit rate:  $0.01 per conversation turn
With 0% cache hit rate:   $1.50+ per conversation turn
Difference:               150x
```

This single number drives the entire design of this suite. Cache hit rate is **the most impactful cost lever** in any LLM deployment, and most systems treat it as a one-time setup rather than a continuously monitored metric.

---

## ✨ Key Features — Highlights

### 📊 Real-Time Cost Coverage

| Before This Skill | After This Skill |
|-----------------|-----------------|
| 51.6% of tokens had no cost tracking | **0.0% blind spot** ✅ |
| Cost showed $0 for WeChat/CLI sessions | **Full cost attribution** for all 6 sources |
| Unknown if pricing table was missing models | **Auto-detected + filled** missing pricing entries |

### 🔍 Cache Anomaly Detection

- Detects sessions with **abnormally low cache hit rates** (<50%)
- Identifies **root cause** for each cache miss (fresh session, prompt change, skill install)
- Calculates **wasted tokens** — what those sessions would have cost with normal caching
- **14 anomalies found in 30 days**, $6.28 in potential waste flagged

### 🕵️ Cache Killer Scanner

Scans SKILL.md files and Hermes system prompts for:

| Killer | Impact | Real Case |
|--------|--------|-----------|
| 🔴 **Timestamps** in system prompt | Cache rate → 0% | Found in 3 skill files |
| 🟡 **User IDs** at wrong position | Each user = unique prefix, no sharing | Team moved 300 tokens → 23% → 71% hit rate |
| 🟡 **JSON sort_keys missing** | Same data, different hash, no cache hit | Found in 7+ skill files |

### 👴 Session Lifecycle Management

- Tracks **message count** and **cost** per session
- Recommends "turn the page" when session exceeds **400 messages or $1.00**
- **870-message session** cost $4.91 vs 617-message session at $0.41 — **12x difference**
- Tracks **inheritance chain** — parent → child → grandchild cache invalidation tax

### 💰 Monthly Budget Tracking

- Set a monthly cap (`"set budget $10"`)
- Tracks daily burn vs. daily allowance
- Projects month-end total and alerts on overspend
- Flags when daily spend exceeds daily budget by 2x+

### 🔧 Toolchain Efficiency

- Monitors **tools per conversation round** (goal: <5)
- Detects **retry loops** — same tool failing 3+ times
- Flags **repeated file reads** — same file read >3x in a session
- Estimates tool call cost: ~80 tokens per call, 5 merged = 320+ saved

### 📈 Trend Tracking & Peak Analysis

- **Daily trend recording** — token consumption by day, by source
- **Automatic peak day review** — identifies Top-3 most expensive days
- **Alert when daily cost exceeds 3x average**
- Cross-profile aggregation: sum costs across all Hermes profiles

---

## 👥 The Team: 1 General + 5 Specialists

Dialogue Actuary isn't a single script — it's a **team of 6 specialized agents**:

```
Dialogue Actuary (General Accountant)
│
├── 🎯 Cache Hit Assistant        → cache-hit-assistant
│    ├ Cache health reports, killer detection, rebuild warnings
│    └ 3 scripts, 1 reference doc
│
├── ✂️ Output Actuary             → output-actuary
│    ├ Output/input ratio, verbose session ranking
│    └ scripts/output-efficiency.py
│
├── 👴 Session Lifecycle Manager  → session-lifecycle-manager
│    ├ Session age warnings, subagent tracking, inheritance chain
│    └ scripts/session-age-check.py
│
├── 💰 Budget Manager             → budget-manager
│    ├ Monthly budget, daily tracking, overspend alerts
│    └ scripts/budget-status.py + BUDGET.md
│
└── 🔧 Toolchain Optimizer        → toolchain-optimizer
│    ├ Tool call density, retry detection, merge suggestions
│    └ scripts/toolchain-stats.py
```

Each specialist is a **separate Hermes skill** that can be loaded independently. Together they provide complete coverage.

---

## 📐 10 Principles of Token Optimization

| # | Principle | Type | Impact |
|---|-----------|------|--------|
| P1 | **Input SNR** — precise paths over fuzzy search | Assistant | Saves 500-3000 tok/call |
| P2 | **Output compression** — no chit-chat, no fluff | Assistant | Saves 40-60% output |
| P3 | **Context management** — load skills on demand | Assistant | Saves thousands/call |
| P4 | **Task grading** — L1 output ≤100 chars, L4 unlimited | Assistant | Matches effort to need |
| P5 | **Decision triage** — local tool > LLM call | Assistant | Prevents waste |
| P6 | **CLI compression** — RTK + Caveman engine | Assistant | Saves 88-92% |
| P7 | **Protocol optimization** — cache rate is sacred | Environment | 96-99% rate = minimal cost |
| P8 | **Budget & trends** — monthly cap, daily alert | Assistant | Prevents bill shock |
| P9 | **Cache invalidation guard** — batch changes, warn before breaking | Assistant | Saves $1.50+ per breach |
| P10 | **Session lifecycle** — turn the page at 400 msgs / $1 cost | Assistant | Prevents 12x cost degradation |

---

## ⚡ 11 Iron Rules (Priority Ordered)

| # | Rule | Execution | Cost of Violation |
|---|------|-----------|-------------------|
| 1 | **Integrity > Savings** | Never lose data for compression | User distrust → full output → more waste |
| 2 | **Direct answers** | No greetings, no rephrasing | 100-500 tok/round wasted |
| 3 | **Structured output** | Tables/lists/JSON > prose | Saves 40-60% |
| 4 | **Precise references** | `read_file` + line > `search_files` | Saves 500-3000 tok/call |
| 5 | **Memory first** | Don't re-query known info | Saves 500+ tok/call |
| 6 | **Compress terminal** | Summarize CLI output before context | Saves 88-92% CLI tok |
| 7 | **Batch operations** | Merge 3+ calls → `execute_code` | Saves 80+ tok/tool |
| 8 | **Don't report proactively** | No cost summaries unless asked | Report itself costs token |
| 9 | **Fail fast** | 3 failures → stop, change approach | Infinite loops waste 10K+ tok |
| 10 | **Cache breach alert** | Identify reason for <50% cache rate | $1.50+ per breach |
| 11 | **Session turnover** | >400 msgs or >$1 → suggest fresh session | Long sessions cost 12x more |

---

## 🏗 Technical Architecture

```
Hermes state.db (SQLite)
│
├── sessions table
│   ├── input_tokens, output_tokens       ← raw token counts
│   ├── cache_read_tokens, cache_write    ← cache performance
│   ├── estimated_cost_usd, actual_cost   ← cost data
│   ├── model, billing_provider           ← pricing context
│   ├── source (tui/cli/weixin/cron/subagent)
│   ├── parent_session_id                 ← inheritance chain
│   └── system_prompt                     ← for skill attribution
│
└── messages table
    ├── tool_name, tool_calls             ← toolchain analysis
    └── finish_reason, timestamp
            │
            ▼
    ┌──────────────────────────────────────────────┐
    │          Dialogue Actuary Scripts             │
    │                                              │
    │  token-usage-estimator.py    ← cost queries  │
    │  token-trend-tracker.py      ← daily trends  │
    │  cache-anomaly-detector.py   ← cache health  │
    │  session-cost-monitor.py     ← aging + audit │
    │  skill-roi-analyzer.py       ← per-skill ROI │
    │  token_utils.py              ← shared module │
    └──────────────────────────────────────────────┘
            │
            ▼
    ┌──────────────────────────────────────────────┐
    │            Specialist Skills                  │
    │                                              │
    │  cache-hit-assistant      → cache focus      │
    │  output-actuary           → output focus     │
    │  session-lifecycle-manager → session focus   │
    │  budget-manager           → budget focus     │
    │  toolchain-optimizer      → tool focus       │
    └──────────────────────────────────────────────┘
```

### Shared Utility Layer

All scripts import from `token_utils.py` for:
- **Unified DB path resolution** (`resolve_db()`) — supports multiple Hermes profiles
- **Safe connection** (`safe_connect()`) — graceful failure, no crashes
- **Consistent formatting** (`fmt_num()`, `fmt_time()`) — 1K/1.5M/2.1B format
- **Token pricing constants** — `$0.14/M input`, `$0.28/M output`, `$0.003/M cache read`
- **Cache rate calculator** — `cache_rate()` with zero-division guard

---

## 🎯 Cache Hit Assistant Deep Dive

The Cache Hit Assistant (`cache-hit-assistant` skill) deserves special attention — it's the most impactful specialist.

### What It Detects

| Detection | Method | Real Impact |
|-----------|--------|-------------|
| Zero-cache sessions | SQL query for `cache_read_tokens=0` | **6 sessions found**, $9.28 waste |
| Low-cache sessions | Ratio check (<50%) | **14 anomalies in 30 days** |
| Cache killer in SKILL.md | Text scan of 120+ skill files | **5 timestamp findings** |
| Cache rebuild cost | Current session cache × pricing | **$17.85 potential rebuild tax** |
| Daily trend comparison | Yesterday vs today cache rate | **1.8pp drop detected** |

### Cache Rebuild Warning

Before each cache-destroying operation (skill install, config change, update), the warner estimates:

```
⚠️ 当前缓存: 31.5M tokens (约 $0.15)
   首轮重建成本: $4.46
   恢复到90%+缓存率: $13.39 (约3轮)
   总缓存税: ~$17.85
   建议: 一次性完成所有安装/变更，别拆成多次
```

### Real Cache Killers Found

Scanning the skill ecosystem found **5+ cache killers**:

1. **`hermes-operations/SKILL.md`** — dynamic timestamp in system prompt
2. **`open-webui-setup/SKILL.md`** — time-based content
3. **`google-workspace` scripts** — `datetime.now()` in tool integration
4. **7+ skills** with `json.dumps` missing `sort_keys=True`
5. **8+ skills** with user ID references in system prompt context

Each killer **permanently reduces cache hit rate** for every conversation using that skill.

---

## 📊 Real-World Impact

### Cost Coverage Transformation

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Token tracking blind spot | **51.6%** | **0.0%** | ✅ Full coverage |
| DeepSeek-v4-flash cost | **$0** (185 sessions) | **$2.83** | ✅ Backfilled |
| WeChat cost visibility | **$0** | **$0.95** | ✅ Tracked |
| CLI cost visibility | **$0** | **$0.12** | ✅ Tracked |
| Cost sources tracked | 2/6 | **6/6** | ✅ Complete |

### Discovered Savings Opportunities

| Finding | Amount | Root Cause |
|---------|--------|------------|
| Skill install cache invalidations | **$14.17** (71% of total) | xyq-skill 8 install attempts |
| Subagent zero-cache overhead | **$4.51** (22.5%) | 21 subagents with no shared cache |
| Session aging degradation | **12x cost** | 870-msg session vs 617-msg |
| Budget overspend | **156%** | Monthly budget $10, actual $25.59 |

---

## 🚀 Quick Start

### Prerequisites

- [Hermes Agent](https://hermes-agent.nousresearch.com) installed
- Hermes `state.db` with session data (auto-populated)

### Installation

```bash
# Install the Dialogue Actuary skill
hermes skills install hermes-token-saver

# (Optional) Install specialist skills
hermes skills install cache-hit-assistant
hermes skills install output-actuary
hermes skills install session-lifecycle-manager
hermes skills install budget-manager
hermes skills install toolchain-optimizer
```

### First Run

```bash
# Check cost coverage
cd ~/.hermes/skills/hermes/hermes-token-saver
python3 scripts/token-usage-estimator.py --coverage

# View today's spending
python3 scripts/token-usage-estimator.py --today

# Run a full audit
python3 scripts/session-cost-monitor.py --audit

# Check cache health
python3 /path/to/cache-hit-assistant/scripts/cache-health-check.py
```

### Auto-Schedule (via Cron)

The 23:59 daily audit cron is automatically registered when you use the `对话精算师每日审计` cron job.

To manually set up:

```bash
hermes cron create \
  --name "Daily Token Audit" \
  --schedule "59 23 * * *" \
  --skill hermes-token-saver \
  --prompt "Run the daily token audit and report"
```

---

## 📖 Commands Reference

### Dialogue Actuary (Core)

| Command | Script | What It Does |
|---------|--------|-------------|
| "查今日" / "今天花了" | `--today` | Today's total token & cost |
| "统计全部" / "总花费" | `--all` | Full lifetime breakdown by source |
| "查成本来源" | `--coverage` | Which sources have cost tracking |
| "查零缓存" | `--zero-cache` | Sessions with 0% cache rate |
| "查趋势" / "最近趋势" | `--view` | 14-day trend of token consumption |
| "精算审计" / "全面审计" | `--audit` | Full system audit (aging + peaks + cache + coverage) |
| "峰值复盘" | `--peak` | Top-3 most expensive days with root cause |
| "按 skill 归因" | `skill-roi-analyzer.py` | Cost attribution per loaded skill |
| "查 session 老化" | `--aging` | Sessions >400 msgs or >$1 cost |
| "本月预算 $X" | Set monthly cap | Tracks daily vs budget |

### Cache Hit Assistant

| Command | Script | What It Does |
|---------|--------|-------------|
| "缓存状态" | `cache-health-check.py` | Today's cache hit rate + vs yesterday |
| "查缓存异常" | `cache-anomaly-detector.py` | Low-cache sessions in last 7 days |
| "查缓存杀手" | `cache-killer-detector.py` | Scans for cache-breaking patterns |
| "这个操作烧缓存吗" | `cache-rebuild-warner.py` | Estimates rebuild cost if cache cleared |

### Specialist Commands

| Specialist | Command | Script |
|-----------|---------|--------|
| Output Actuary | "输出效率" | `output-efficiency.py` |
| Session Lifecycle | "会话年龄" | `session-age-check.py` |
| Budget Manager | "预算状态" | `budget-status.py` |
| Toolchain Optimizer | "工具效率" | `toolchain-stats.py` |

---

## 🔄 Development & Self-Check

The Dialogue Actuary undergoes **10-round self-check cycles** to maintain quality:

### Round Structure

Each round performs 3 tasks:
1. **Logic validation** — full-chain reasoning, find hidden gaps, contradictions, edge cases
2. **Optimization** — identify rough/inefficient/missing modules, provide actionable fixes
3. **Innovation** — brainstorm new features, execution logic, expand capability

### Audit Log (v2.0)

| Round | Blind Spot | Discovery | Fix |
|-------|-----------|-----------|-----|
| D1 | Skill install cache invalidation | xyq-skill installs = $14.17 (71%) | P9 Cache invalidation guard |
| D2 | Subagent zero-cache | 21 subagents = $4.51 (22.5%) | P10 Session lifecycle management |
| D3 | WeChat/CLI cost blind spot | 9 weixin sessions show $0 | `--coverage` detection |
| D4 | Zero-cache silence | 6 sessions at 0-2%, $9.28 total | `cache-anomaly-detector.py` |
| D5 | Session age degradation | 870-msg session costs 12x more | `session-cost-monitor.py --aging` |
| D6 | Cross-profile blind spot | Only default profile tracked | `--cross-profile` flag |
| D7 | Peak day retro missing | $15.90 peak (79%) only noticed after | `session-cost-monitor.py --peak` |
| D8 | Task attribution missing | All subagents show title="?" | Title tagging recommendation |

### Current Version: 2.0.0

---

## 🗺 Roadmap

- [ ] **Cache Warmer** — auto-send warmup request after skill install to pre-build cache
- [ ] **Live Token Dashboard** — real-time `curses` dashboard watching token burn rate
- [ ] **Per-Skill ROI** — rank skills by cost impact (infrastructure ready, awaiting data)
- [ ] **Cross-Session Cache Domain Analyzer** — identify parent-child cache breaks
- [x] **Cache Hit Assistant** — dedicated cache monitoring
- [x] **Budget Manager** — monthly cap + daily tracking
- [x] **Session Lifecycle Manager** — auto turn-page recommendations

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

## 🙏 Acknowledgments

- **Hermes Agent** ([Nous Research](https://nousresearch.com)) — the agent framework this skill extends
- **RTK + Caveman** — CLI output compression techniques (88-92% savings)
- **DeepSeek API Docs** — cache prefix unit mechanics documentation
- **KV-Cache Aware Prompt Engineering** (Ankit Sinha) — 65% latency improvement insights
- **Prompt Cache Hit Rate** (Tian Pan) — production metric monitoring framework

---

<p align="center">
  <i>Token is money. Spend it precisely.</i>
</p>
