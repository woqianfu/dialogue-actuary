#!/usr/bin/env python3
"""
Session Cost Monitor — 对话精算师 v2.0
检测 session 年龄退化、自动峰值复盘、全面审计。

用法：
  python3 session-cost-monitor.py --aging          ← session 老化检测
  python3 session-cost-monitor.py --peak            ← 峰值日复盘（Top-3 最贵日）
  python3 session-cost-monitor.py --audit           ← 全面审计（老化+峰值+缓存+覆盖）
  python3 session-cost-monitor.py --cross-profile   ← 跨 profile 汇总
"""

import sqlite3, json, sys, os
from pathlib import Path
from datetime import datetime, timezone, timedelta

STATE_DB = Path.home() / ".hermes" / "state.db"
PROFILES_DIR = Path.home() / ".hermes" / "profiles"


def fmt_time(ts):
    return datetime.fromtimestamp(ts).strftime("%m-%d %H:%M") if ts else "-"


def get_db_paths():
    paths = {"default": STATE_DB}
    if PROFILES_DIR.exists():
        for p in PROFILES_DIR.iterdir():
            db = p / "state.db"
            if db.exists():
                paths[p.name] = db
    return paths


def query(db, sql, params=()):
    try:
        conn = sqlite3.connect(str(db))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []


def detect_aging(days=30, output_json=False):
    """检测 session 老化 — 消息数 > 400 或成本 > $1"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = query(STATE_DB, """
        SELECT id, source, title, started_at, message_count,
               input_tokens, output_tokens, cache_read_tokens,
               estimated_cost_usd, actual_cost_usd
        FROM sessions
        WHERE started_at >= ?
        ORDER BY message_count DESC
    """, (cutoff.timestamp(),))

    over_msg = []
    over_cost = []
    for r in rows:
        msg = r["message_count"] or 0
        cost = r["estimated_cost_usd"] or r["actual_cost_usd"] or 0
        if msg > 400:
            over_msg.append(r)
        if cost > 1.0:
            over_cost.append(r)

    if output_json:
        print(json.dumps({
            "total_sessions": len(rows),
            "over_400_messages": len(over_msg),
            "over_1_dollar": len(over_cost),
        }, ensure_ascii=False))
        return

    print(f"📊 **Session 老化检测** — 近 {days} 天\n")
    print(f"├ 检查: {len(rows)} tui session")
    print(f"├ 消息数 > 400: {len(over_msg)}")
    print(f"├ 成本 > $1.00: {len(over_cost)}")

    if over_msg:
        print(f"\n**⚠️ 高消息数 session（建议翻篇）**")
        for r in over_msg[:5]:
            msg = r["message_count"] or 0
            cost = r["estimated_cost_usd"] or r["actual_cost_usd"] or 0
            cache = r["cache_read_tokens"] or 0
            inp = r["input_tokens"] or 0
            title = (r["title"] or "?")[:40]
            efficiency = "🟢" if msg > 0 and (r["output_tokens"] or 0) / msg > 100 else "🔴"
            print(f"├ {efficiency} {msg} 条消息 | ${cost:.4f} | {title}")
            print(f"│ 输入:{inp:,} 缓存:{cache:,} | {fmt_time(r['started_at'])}")
    if over_cost:
        print(f"\n**💸 高成本 session（建议翻篇）**")
        for r in over_cost[:5]:
            cost = r["estimated_cost_usd"] or r["actual_cost_usd"] or 0
            msg = r["message_count"] or 0
            title = (r["title"] or "?")[:40]
            print(f"├ ${cost:.4f} | {msg} 条消息 | {title}")
    if not over_msg and not over_cost:
        print("\n✅ 所有 session 健康")

    print(f"\n**建议**: 消息 > 400 或成本 > $1 时开新对话。按当前退化率，这些 session 可节省 ~${sum(r['estimated_cost_usd'] or r['actual_cost_usd'] or 0 for r in over_msg[:3])*0.5:.2f}")


def peak_review(days=60, output_json=False):
    """峰值日复盘 — 找出 Top-3 最贵日"""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    rows = query(STATE_DB, """
        SELECT started_at, estimated_cost_usd, actual_cost_usd,
               input_tokens, output_tokens, source, title
        FROM sessions
        WHERE started_at >= ? AND (estimated_cost_usd > 0 OR actual_cost_usd > 0)
        ORDER BY started_at
    """, (cutoff.timestamp(),))

    daily = {}
    for r in rows:
        day = datetime.fromtimestamp(r["started_at"]).strftime("%Y-%m-%d")
        cost = r["estimated_cost_usd"] or r["actual_cost_usd"] or 0
        inp = r["input_tokens"] or 0
        if day not in daily:
            daily[day] = {"cost": 0, "sessions": 0, "input": 0, "sources": set()}
        daily[day]["cost"] += cost
        daily[day]["sessions"] += 1
        daily[day]["input"] += inp
        daily[day]["sources"].add(r["source"] or "?")

    sorted_days = sorted(daily.items(), key=lambda x: -x[1]["cost"])
    total_cost = sum(d["cost"] for d in daily.values())

    if output_json:
        print(json.dumps({
            "days_count": len(sorted_days),
            "total_cost": round(total_cost, 4),
            "top_peaks": [{"date": d, "cost": round(v["cost"], 4),
                          "pct": round(v["cost"]/total_cost*100, 1),
                          "sessions": v["sessions"]} for d, v in sorted_days[:5]]
        }, ensure_ascii=False))
        return

    print(f"📊 **峰值日复盘** — 近 {days} 天\n")
    print(f"├ 有成本日数: {len(sorted_days)} 天 | 总成本: ${total_cost:.4f}\n")

    for day, stats in sorted_days[:5]:
        pct = stats["cost"] / total_cost * 100 if total_cost > 0 else 0
        avg_per_session = stats["cost"] / stats["sessions"] if stats["sessions"] > 0 else 0
        sources = ", ".join(sorted(stats["sources"]))
        flag = " ⚠️" if pct > 20 else (" 🔶" if pct > 10 else "")
        print(f"{'🥇' if sorted_days.index((day, stats))==0 else '🥈' if sorted_days.index((day, stats))==1 else '🥉' if sorted_days.index((day, stats))==2 else '   '} {day} | **${stats['cost']:.4f}** ({pct:.0f}%){flag}")
        print(f"├ Session: {stats['sessions']} | 输入: {stats['input']:,} | 单均: ${avg_per_session:.4f}")
        print(f"└ 来源: {sources}\n")

    # Identify root cause of top peak
    peak_day, peak_stats = sorted_days[0]
    print(f"**峰值根因分析**: {peak_day} (${peak_stats['cost']:.4f}, {peak_stats['cost']/total_cost*100:.0f}%)")
    peak_rows = [r for r in rows if datetime.fromtimestamp(r["started_at"]).strftime("%Y-%m-%d") == peak_day]
    peak_rows.sort(key=lambda r: -(r["estimated_cost_usd"] or r["actual_cost_usd"] or 0))
    for r in peak_rows[:5]:
        cost = r["estimated_cost_usd"] or r["actual_cost_usd"] or 0
        title = (r["title"] or "?")[:50]
        print(f"├ ${cost:.4f} | {title}")


def full_audit(output_json=False):
    """全面审计：合并老化 + 峰值 + 缓存异常"""
    aging = query(STATE_DB, """
        SELECT COUNT(*) as total,
               SUM(CASE WHEN message_count > 400 THEN 1 ELSE 0 END) as over_msg,
               SUM(CASE WHEN (estimated_cost_usd > 1.0 OR actual_cost_usd > 1.0) THEN 1 ELSE 0 END) as over_cost
        FROM sessions WHERE source = 'tui'
    """)

    peaks = query(STATE_DB, """
        SELECT DATE(datetime(started_at, 'unixepoch')) as day,
               SUM(estimated_cost_usd) as total_cost
        FROM sessions WHERE estimated_cost_usd > 0
        GROUP BY day ORDER BY total_cost DESC LIMIT 3
    """)

    coverage = query(STATE_DB, """
        SELECT source, COUNT(*) as sessions,
               SUM(input_tokens + output_tokens) as tokens,
               SUM(cache_read_tokens) as cache,
               SUM(estimated_cost_usd) as cost_est,
               SUM(actual_cost_usd) as cost_act
        FROM sessions GROUP BY source ORDER BY sessions DESC
    """)

    total = query(STATE_DB, """
        SELECT COUNT(*) as total, SUM(input_tokens) as inp, SUM(output_tokens) as out,
               SUM(cache_read_tokens) as cache,
               SUM(estimated_cost_usd) as cost_est, SUM(actual_cost_usd) as cost_act
        FROM sessions
    """)[0]

    if output_json:
        print(json.dumps({
            "total_sessions": total["total"],
            "total_cost": round((total["cost_est"] or 0) + (total["cost_act"] or 0), 4),
            "aging": {"over_400_msg": aging[0]["over_msg"] if aging else 0},
            "peaks": [{"day": p["day"], "cost": round(p["total_cost"], 4)} for p in peaks],
            "coverage": {c["source"]: {"sessions": c["sessions"], "has_cost": c["cost_est"] is not None and c["cost_est"] > 0} for c in coverage},
            "cache_read_pct": round(coverage[0]["cache"] / (coverage[0]["tokens"] + coverage[0]["cache"]) * 100, 1) if coverage and coverage[0]["tokens"] + coverage[0]["cache"] > 0 else 0,
        }, ensure_ascii=False, indent=2))
        return

    t_inp = total["inp"] or 0
    t_out = total["out"] or 0
    t_cache = total["cache"] or 0
    t_cost = (total["cost_est"] or total["cost_act"] or 0)

    print("📊 **对话精算师 · 全面审计**\n")
    print(f"**总览**: {total['total']} session | 输入 {t_inp:,} | 输出 {t_out:,} | 缓存 {t_cache:,} | 成本 ${t_cost:.4f}\n")

    # 缓存率
    cache_pct = round(t_cache / (t_inp + t_out + t_cache) * 100, 1) if (t_inp + t_out + t_cache) > 0 else 0
    print(f"**缓存率**: {cache_pct}% {'✅' if cache_pct > 90 else '⚠️'}")

    # 老化
    if aging:
        print(f"**Aging**: {aging[0]['over_msg']} session 消息 > 400 | {aging[0]['over_cost']} session 成本 > $1")

    # 峰值
    if peaks:
        print(f"**Top-3 峰值**: " + " | ".join(f"{p['day']} ${p['total_cost']:.4f}" for p in peaks))

    # 覆盖率
    blind_sources = [c["source"] for c in coverage if (c["cost_est"] is None or c["cost_est"] == 0) and c["tokens"] > 0]
    if blind_sources:
        print(f"**⚠️ 成本盲区**: {', '.join(blind_sources)} — 有 token 消耗但成本为 $0")

    # 零缓存
    zero_cache = query(STATE_DB, """
        SELECT COUNT(*) as cnt,
               SUM(estimated_cost_usd) as cost
        FROM sessions WHERE cache_read_tokens = 0 AND input_tokens > 100000
    """)
    if zero_cache and zero_cache[0]["cnt"] > 0:
        print(f"**⚠️ 零缓存大 session**: {zero_cache[0]['cnt']} 个 (缓存率 0%，输入 >100K)")
        print(f"├ 潜在浪费 ≈ ${zero_cache[0]['cost']:.4f}")

    print("\n✅ 审计完成")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--aging", action="store_true")
    parser.add_argument("--peak", action="store_true")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--cross-profile", action="store_true")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.audit:
        full_audit(args.json)
    elif args.peak:
        peak_review(args.days, args.json)
    elif args.aging:
        detect_aging(args.days, args.json)
    elif args.cross_profile:
        paths = get_db_paths()
        print(f"📊 **跨 Profile 汇总 ({len(paths)} profiles)**\n")
        total_cost = 0
        for name, db in paths.items():
            r = query(db, "SELECT SUM(estimated_cost_usd) as cost, SUM(input_tokens) as inp FROM sessions")
            if r:
                cost = r[0]["cost"] or 0
                inp = r[0]["inp"] or 0
                total_cost += cost
                if cost > 0:
                    print(f"├ {name}: ${cost:.4f} | {inp:,} 输入 token")
        print(f"\n└ **合计**: ${total_cost:.4f}")
    else:
        parser.print_help()
