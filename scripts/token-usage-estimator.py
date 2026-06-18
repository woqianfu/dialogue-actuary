#!/usr/bin/env python3
"""
Token Usage Estimator — Hermes Token Saver 配套脚本
直接读取 Hermes state.db 中原生的 token 统计字段

用法：
  python3 token-usage-estimator.py                    ← 当前 session（最近1个）
  python3 token-usage-estimator.py --recent N          ← 最近 N 个 session
  python3 token-usage-estimator.py --session <id>      ← 指定 session
  python3 token-usage-estimator.py --all               ← 全部 session 汇总
  python3 token-usage-estimator.py --today              ← 今日消耗汇总
  python3 token-usage-estimator.py --week              ← 本周消耗汇总
  python3 token-usage-estimator.py --month             ← 本月消耗汇总
  python3 token-usage-estimator.py --json              ← JSON 输出（供其他工具消费）
  python3 token-usage-estimator.py --alert N           ← 今日是否超过日均 N 倍
  python3 token-usage-estimator.py --trend             ← 查看近期趋势
  python3 token-usage-estimator.py --profile <name>    ← 指定 profile
"""

import sqlite3
import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

STATE_DB = Path.home() / ".hermes" / "state.db"
PROFILES_DIR = Path.home() / ".hermes" / "profiles"

FIELDS = [
    "id", "source", "title", "started_at", "ended_at",
    "message_count", "tool_call_count",
    "input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens",
    "reasoning_tokens", "api_call_count",
    "estimated_cost_usd", "actual_cost_usd", "cost_status", "cost_source",
    "pricing_version", "billing_provider",
]


def resolve_db():
    """根据当前 profile 确定 state.db 路径"""
    profile = os.environ.get("HERMES_PROFILE") or os.environ.get("HERMES_ACTIVE_PROFILE")
    if profile and (PROFILES_DIR / profile / "state.db").exists():
        return PROFILES_DIR / profile / "state.db"
    return STATE_DB


def safe_connect(db_path):
    """安全连接数据库"""
    path = str(resolve_db() if db_path is None else db_path)
    if not Path(path).exists():
        print(f"❌ 数据库不存在: {path}")
        sys.exit(1)
    try:
        conn = sqlite3.connect(path)
        conn.execute("SELECT 1 FROM sessions LIMIT 1")
        return conn
    except sqlite3.OperationalError as e:
        print(f"❌ 数据库不可访问: {e}")
        sys.exit(1)


def fmt_time(ts):
    if not ts:
        return "-"
    return datetime.fromtimestamp(ts).strftime("%m-%d %H:%M")


def query_sessions(where_clause="", params=(), limit=None, db_path=None):
    """查询 session token 数据"""
    conn = safe_connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    fields_str = ", ".join(FIELDS)
    sql = f"SELECT {fields_str} FROM sessions"
    if where_clause:
        sql += f" WHERE {where_clause}"
    sql += " ORDER BY started_at DESC"
    if limit:
        sql += f" LIMIT {limit}"
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def format_session(s, index=None):
    prefix = f"**#{index}** " if index else ""
    sid = s["id"][:8] if s["id"] else "?"
    inp = s["input_tokens"] or 0
    out = s["output_tokens"] or 0
    total = inp + out + (s["cache_read_tokens"] or 0) + (s["cache_write_tokens"] or 0)
    cost = s["estimated_cost_usd"] or s["actual_cost_usd"] or 0
    return (
        f"💰 Session `{sid}` — {fmt_time(s['started_at'])}\n"
        f"├ 来源: {s['source'] or '-'} | 消息: {s['message_count'] or 0} | 工具: {s['tool_call_count'] or 0}\n"
        f"├ 输入: {inp:,} | 输出: {out:,} | 缓存读: {s['cache_read_tokens'] or 0:,}\n"
        f"├ 推理: {s['reasoning_tokens'] or 0:,} | API: {s['api_call_count'] or 0} 次\n"
        f"├ 总 Token: {total:,}\n"
        f"└ 成本: **${cost:.4f}**\n"
    )


def build_aggregate(rows, label=""):
    """从多行 session 构建聚合摘要"""
    total_inp = sum(r["input_tokens"] or 0 for r in rows)
    total_out = sum(r["output_tokens"] or 0 for r in rows)
    total_cache = sum((r["cache_read_tokens"] or 0) + (r["cache_write_tokens"] or 0) for r in rows)
    total_cost = sum(r["estimated_cost_usd"] or r["actual_cost_usd"] or 0 for r in rows)
    total_api = sum(r["api_call_count"] or 0 for r in rows)
    total_tools = sum(r["tool_call_count"] or 0 for r in rows)
    sessions = len(rows)
    return {
        "label": label,
        "sessions": sessions,
        "input_tokens": total_inp,
        "output_tokens": total_out,
        "cache_tokens": total_cache,
        "api_calls": total_api,
        "tools": total_tools,
        "cost": round(total_cost, 6),
    }


def print_aggregate(agg, indent=True):
    p = "├ " if indent else ""
    print(f"{p}Session: {agg['sessions']} | 输入: {agg['input_tokens']:,} | 输出: {agg['output_tokens']:,} | "
          f"缓存: {agg['cache_tokens']:,} | API: {agg['api_calls']} | 工具: {agg['tools']} | "
          f"成本: **${agg['cost']:.4f}**")


def cmd_session(session_id):
    rows = query_sessions("id = ?", (session_id,))
    if not rows:
        print(f"❌ Session 未找到: {session_id}")
        return
    print("📊 **Token 消耗明细**\n")
    print(format_session(rows[0]))


def cmd_recent(n=5, output_json=False):
    rows = query_sessions(limit=n)
    if not rows:
        print("❌ 无 session 数据")
        return
    if output_json:
        print(json.dumps([build_aggregate(rows, f"recent_{n}")], ensure_ascii=False))
        return
    print(f"📊 **最近 {len(rows)} 个 Session Token 消耗**\n")
    for i, s in enumerate(rows, 1):
        print(format_session(s, i))
    agg = build_aggregate(rows)
    print(f"**小计**: {agg['input_tokens']+agg['output_tokens']:,} token = ${agg['cost']:.4f}")


def cmd_day_range(days=1, label="今日", output_json=False):
    """查询最近 N 天的汇总"""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    rows = query_sessions("started_at >= ?", (start.timestamp(),))
    if not rows:
        msg = f"📊 **{label}**: 暂无数据"
        if output_json:
            print(json.dumps({"label": label, "sessions": 0, "cost": 0}, ensure_ascii=False))
        else:
            print(msg)
        return
    agg = build_aggregate(rows, label)
    if output_json:
        print(json.dumps(agg, ensure_ascii=False))
        return
    print(f"📊 **{label} Token 汇总** — {agg['sessions']} session\n")
    print_aggregate(agg, False)


def alert_check(threshold=3.0):
    """检查今日成本是否超过近期日均的 threshold 倍"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    days_ago_7 = today_start - timedelta(days=7)

    today_rows = query_sessions("started_at >= ?", (today_start.timestamp(),))
    today_cost = sum(r["estimated_cost_usd"] or r["actual_cost_usd"] or 0 for r in today_rows)

    recent_rows = query_sessions("started_at >= ? AND started_at < ?",
                                  (days_ago_7.timestamp(), today_start.timestamp()))
    # Use fixed 7-day window instead of unique days with data
    day_count = 7
    recent_cost = sum(r["estimated_cost_usd"] or r["actual_cost_usd"] or 0 for r in recent_rows)
    daily_avg = recent_cost / day_count

    if daily_avg > 0 and today_cost > daily_avg * threshold:
        print(f"⚠️ **Token 成本告警**")
        print(f"├ 今日: **${today_cost:.4f}**")
        print(f"├ 近{day_count}日均: ${daily_avg:.4f}")
        print(f"├ 倍率: {today_cost/daily_avg:.1f}x (阈值: {threshold}x)")
        print(f"└ 建议: 检查今日是否有大量任务或异常循环")
    elif today_cost == 0:
        print(f"📊 今日尚无 token 消耗数据")
    else:
        print(f"✅ 今日 ${today_cost:.4f} / 日均 ${daily_avg:.4f} (比值 {today_cost/daily_avg:.1f}x, 阈值 {threshold}x)")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Hermes Token 估算（原生 DB 字段）")
    parser.add_argument("--session", help="Session ID")
    parser.add_argument("--recent", nargs="?", const=5, type=int, default=None, help="最近 N 个 session (默认 5)")
    parser.add_argument("--today", action="store_true", help="今日汇总")
    parser.add_argument("--week", action="store_true", help="本周汇总")
    parser.add_argument("--month", action="store_true", help="本月汇总")
    parser.add_argument("--all", action="store_true", help="全部汇总")
    parser.add_argument("--profile", help="指定 profile")
    parser.add_argument("--reasoning", action="store_true", help="查看推理 token 占比")
    parser.add_argument("--trend", action="store_true", help="查看近期趋势（委托 trend tracker）")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    parser.add_argument("--alert", nargs="?", const=3.0, type=float, default=None,
                        help="检查今日成本是否超过日均 N 倍 (默认 3)")
    parser.add_argument("--zero-cache", action="store_true",
                        help="列出缓存率为 0% 的 session（缓存完全失效）")
    parser.add_argument("--coverage", action="store_true",
                        help="检查成本来源覆盖率 — 哪些 source 有/无成本数据")

    args = parser.parse_args()

    # 全局 DB 路径覆盖
    db_path = None
    if args.profile:
        pdb = PROFILES_DIR / args.profile / "state.db"
        if pdb.exists():
            db_path = pdb
        else:
            print(f"❌ Profile '{args.profile}' 不存在或没有 state.db")
            sys.exit(1)

    if args.reasoning:
        conn = safe_connect(db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT SUM(reasoning_tokens), SUM(input_tokens + output_tokens),
                   ROUND(CAST(SUM(reasoning_tokens) AS REAL) / NULLIF(SUM(input_tokens + output_tokens), 0) * 100, 1)
            FROM sessions WHERE reasoning_tokens > 0
        """)
        r = cur.fetchone()
        if r and r[0] and r[0] > 0:
            print(f"📊 **推理 Token 占比**\n├ 推理: {r[0]:,} / 总计: {r[1]:,} = {r[2]}%")
            cur.execute("""
                SELECT source, SUM(reasoning_tokens), SUM(input_tokens+output_tokens),
                  ROUND(CAST(SUM(reasoning_tokens) AS REAL)/NULLIF(SUM(input_tokens+output_tokens),0)*100,1)
                FROM sessions WHERE reasoning_tokens > 0
                GROUP BY source ORDER BY SUM(reasoning_tokens) DESC
            """)
            for row in cur.fetchall():
                print(f"├ {row[0]}: {row[1]:,} / {row[2]:,} = {row[3]}%")
            print("└ (完)")
        else:
            print("📊 当前模型/环境中没有推理 token 数据")
        conn.close()
        sys.exit(0)

    if args.trend:
        from subprocess import run
        trend_script = Path(__file__).parent / "token-trend-tracker.py"
        result = run([sys.executable, str(trend_script), "--view"], capture_output=True, text=True)
        print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="")
        sys.exit(0)

    if args.alert is not None:
        alert_check(args.alert)
        sys.exit(0)

    if args.session:
        cmd_session(args.session)
    elif args.today:
        cmd_day_range(1, "今日", args.json)
    elif args.week:
        cmd_day_range(7, "本周", args.json)
    elif args.month:
        cmd_day_range(30, "本月", args.json)
    elif args.all:
        rows = query_sessions(db_path=db_path)
        if not rows:
            print("❌ 无数据")
            sys.exit(0)
        agg = build_aggregate(rows, "全量")
        if args.json:
            print(json.dumps(agg, ensure_ascii=False))
        else:
            print(f"📊 **全量 Token 汇总** — {agg['sessions']} session\n")
            # 按来源分类
            sources = {}
            for s in rows:
                src = s["source"] or "unknown"
                if src not in sources:
                    sources[src] = {"count": 0, "cost": 0, "tokens": 0}
                sources[src]["count"] += 1
                sources[src]["cost"] += s["estimated_cost_usd"] or s["actual_cost_usd"] or 0
                sources[src]["tokens"] += (s["input_tokens"] or 0) + (s["output_tokens"] or 0)
            print(f"├ 总输入: {agg['input_tokens']:,} | 总输出: {agg['output_tokens']:,} | "
                  f"缓存: {agg['cache_tokens']:,}")
            print(f"├ API: {agg['api_calls']:,} 次 | 工具: {agg['tools']:,}")
            print(f"└ 总成本: **${agg['cost']:.4f}**\n")
            print("**按来源分类:**")
            for src, stats in sorted(sources.items(), key=lambda x: -x[1]["cost"]):
                print(f"├ {src}: {stats['count']} sessions, {stats['tokens']:,} token, ${stats['cost']:.4f}")
            print("└ (完)")
    elif args.recent is not None:
        cmd_recent(args.recent, args.json)
    elif args.zero_cache:
        rows = query_sessions("cache_read_tokens = 0 AND input_tokens > 0", limit=20)
        if not rows:
            print("📊 无零缓存 session（缓存率 0% 且输入 > 0 的 session）")
        else:
            total_cost = sum(r["estimated_cost_usd"] or r["actual_cost_usd"] or 0 for r in rows)
            print(f"⚠️ **零缓存 Session ({len(rows)})** — 缓存率 0%，潜在浪费 ${total_cost:.4f}\n")
            for s in rows:
                cost = s["estimated_cost_usd"] or s["actual_cost_usd"] or 0
                title = (s["title"] or "?")[:40]
                inp = s["input_tokens"] or 0
                out = s["output_tokens"] or 0
                msgs = s["message_count"] or 0
                src = s["source"] or "?"
                print(f"├ {src} ${cost:.4f} | inp {inp:,} out {out:,} msgs {msgs} | {title}")
            print(f"\n**浪费估算**: 若正常缓存(96-99%)，输入可从 ~{sum(r['input_tokens'] or 0 for r in rows):,} 降至 ~{round(sum(r['input_tokens'] or 0 for r in rows)*0.03):,} token，节省 ~${total_cost*0.9:.4f}")
    elif args.coverage:
        rows = query_sessions("1=1", limit=None)
        sources = {}
        for s in rows:
            src = s["source"] or "unknown"
            if src not in sources:
                sources[src] = {"sessions": 0, "tokens": 0, "cost": 0}
            sources[src]["sessions"] += 1
            sources[src]["tokens"] += (s["input_tokens"] or 0) + (s["output_tokens"] or 0)
            sources[src]["cost"] += s["estimated_cost_usd"] or s["actual_cost_usd"] or 0
        print("📊 **成本来源覆盖率**\n")
        print(f"| 来源 | Sessions | Token | 显示成本 | 状态 |")
        print(f"|------|----------|-------|---------|------|")
        for src, stats in sorted(sources.items(), key=lambda x: -x[1]["tokens"]):
            has_tokens = stats["tokens"] > 0
            has_cost = stats["cost"] > 0
            if has_tokens and has_cost:
                status = "✅"
            elif has_tokens and not has_cost:
                status = "⚠️"
            else:
                status = "○"
            print(f"| {src} | {stats['sessions']} | {stats['tokens']:,} | ${stats['cost']:.4f} | {status} |")
        blind = sum(1 for v in sources.values() if v["cost"] == 0 and v["tokens"] > 0)
        tracked = sum(1 for v in sources.values() if v["cost"] > 0)
        no_tokens = sum(1 for v in sources.values() if v["tokens"] == 0)
        total_tokens = sum(v["tokens"] for v in sources.values())
        blind_tokens = sum(v["tokens"] for v in sources.values() if v["cost"] == 0)
        print(f"\n**覆盖率**: ✅{tracked} / ⚠️{blind} / ○{no_tokens} 来源")
        print(f"**盲区 token**: {blind_tokens:,} / {total_tokens:,} ({blind_tokens/total_tokens*100:.1f}%)")
    else:
        cmd_recent(1, args.json)
