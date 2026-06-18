#!/usr/bin/env python3
"""
Token Trend Tracker — 对话精算师 Token 趋势追踪
每天记录 token 消耗趋势，供精算师查询。

用法：
  python3 token-trend-tracker.py              ← 记录今日并追加到趋势日志（零数据日跳过）
  python3 token-trend-tracker.py --view       ← 查看最近 7 天趋势
  python3 token-trend-tracker.py --summary    ← 输出简要总结（供精算师用）
  python3 token-trend-tracker.py --alert N    ← 今日成本是否超过日均 N 倍
"""

import sqlite3
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

STATE_DB = Path.home() / ".hermes" / "state.db"
TREND_DIR = Path.home() / ".hermes" / "hermes-token-saver"
TREND_FILE = TREND_DIR / "TOKEN_TRENDS.md"
PROFILES_DIR = Path.home() / ".hermes" / "profiles"


def resolve_db():
    profile = os.environ.get("HERMES_PROFILE") or os.environ.get("HERMES_ACTIVE_PROFILE")
    if profile and (PROFILES_DIR / profile / "state.db").exists():
        return PROFILES_DIR / profile / "state.db"
    return STATE_DB


def safe_connect(db_path=None):
    db = resolve_db() if db_path is None else db_path
    if not Path(db).exists():
        return None
    try:
        conn = sqlite3.connect(str(db))
        conn.execute("SELECT 1 FROM sessions LIMIT 1")
        return conn
    except sqlite3.OperationalError:
        return None


def get_daily_stats(days=7):
    """获取最近 N 天的每日 token 统计"""
    conn = safe_connect()
    if not conn:
        return []
    cur = conn.cursor()
    now = datetime.now(timezone.utc)
    results = []
    for i in range(days - 1, -1, -1):
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        cur.execute("""
            SELECT COUNT(*), SUM(input_tokens), SUM(output_tokens),
                   SUM(cache_read_tokens), SUM(cache_write_tokens),
                   SUM(reasoning_tokens), SUM(api_call_count),
                   SUM(estimated_cost_usd), SUM(tool_call_count)
            FROM sessions WHERE started_at >= ? AND started_at < ?
        """, (day_start.timestamp(), day_end.timestamp()))
        row = cur.fetchone()
        s = row[0] or 0; inp = row[1] or 0; out = row[2] or 0
        cache_r = row[3] or 0; cache_w = row[4] or 0
        reasoning = row[5] or 0; api = row[6] or 0
        cost = row[7] or 0; tools = row[8] or 0
        total = inp + out + cache_r + cache_w
        results.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "weekday": day_start.strftime("%a"),
            "sessions": s, "input_tokens": inp, "output_tokens": out,
            "cache_read": cache_r, "cache_write": cache_w,
            "reasoning": reasoning, "api_calls": api, "cost": cost,
            "tools": tools, "total_tokens": total,
            "cache_ratio": round(cache_r / (inp + out + cache_r) * 100, 1) if (inp + out + cache_r) > 0 else 0,
        })
    conn.close()
    return results


def record_today():
    """记录今日数据到趋势文件"""
    TREND_DIR.mkdir(parents=True, exist_ok=True)
    today = get_daily_stats(1)[0]

    # 零数据日跳过
    if today["sessions"] == 0:
        return None

    existing = {}
    if TREND_FILE.exists():
        content = TREND_FILE.read_text()
        for line in content.split("\n"):
            if line.startswith("| ") and not line.startswith("| 日期") and not line.startswith("|---"):
                parts = line.split("|")
                if len(parts) >= 4:
                    date = parts[1].strip()
                    if date and len(date) == 10:
                        existing[date] = line

    cost_str = f"${today['cost']:.4f}" if today['cost'] > 0 else "$0"
    new_line = (
        f"| {today['date']} | {today['weekday']} | {today['sessions']} | "
        f"{today['input_tokens']:,} | {today['output_tokens']:,} | "
        f"{today['cache_read']:,} | {today['cache_ratio']}% | "
        f"{today['api_calls']} | {today['tools']} | "
        f"{today['total_tokens']:,} | {cost_str} |"
    )
    existing[today["date"]] = new_line
    sorted_dates = sorted(existing.keys(), reverse=True)

    # 检查文件是否已有表头
    has_header = TREND_FILE.exists() and "| 日期" in TREND_FILE.read_text()

    lines = []
    if not has_header:
        lines.append(
            "---\n"
            f"> 自动生成：对话精算师 Token 趋势追踪（{today['date']} 初始化）\n"
            "> 来源：state.db 原生字段\n\n"
            "| 日期 | 星期 | Session | 输入 Token | 输出 Token | "
            "缓存读 | 缓存率 | API 次数 | 工具调用 | 总 Token | 成本 |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|\n"
        )
    for d in sorted_dates:
        lines.append(existing[d] + "\n")

    TREND_FILE.write_text("".join(lines))
    return today


def view_trend(days=7):
    """查看最近 N 天趋势"""
    stats = get_daily_stats(days)
    if not stats or all(s["sessions"] == 0 for s in stats):
        print(f"📊 近 {days} 天无数据")
        return

    print(f"📊 **Token 趋势 (近 {days} 天)**\n")
    print(f"| 日期 | 星期 | Session | 输入 | 输出 | 缓存读 | 缓存率 | API | 工具 | 总计 | 成本 |")
    print(f"|-----|------|--------|------|------|--------|--------|-----|------|------|------|")

    total_cost = 0
    non_zero_days = []
    for s in stats:
        if s["sessions"] == 0:
            continue
        non_zero_days.append(s)
        cost_str = f"${s['cost']:.4f}" if s['cost'] > 0 else "$0"
        print(f"| {s['date']} | {s['weekday']} | {s['sessions']} | "
              f"{s['input_tokens']:,} | {s['output_tokens']:,} | "
              f"{s['cache_read']:,} | {s['cache_ratio']}% | "
              f"{s['api_calls']} | {s['tools']} | "
              f"{s['total_tokens']:,} | {cost_str} |")
        total_cost += s['cost']

    print(f"\n**期间总成本**: ${total_cost:.4f}")

    if len(non_zero_days) >= 2:
        first, last = non_zero_days[0], non_zero_days[-1]
        days_count = len(non_zero_days)
        avg_cost = total_cost / days_count
        # 查找峰值
        peak = max(non_zero_days, key=lambda x: x["cost"])
        peak_pct = peak["cost"] / total_cost * 100 if total_cost > 0 else 0
        print(f"**日均**: ${avg_cost:.4f} | **峰值**: {peak['date']} ${peak['cost']:.4f} ({peak_pct:.0f}%)")
        if first["total_tokens"] > 0 and last["total_tokens"] > 0:
            change = (last["total_tokens"] - first["total_tokens"]) / first["total_tokens"] * 100
            direction = "📈 上升" if change > 0 else "📉 下降"
            print(f"**趋势**: 首日 {first['total_tokens']:,} → 末日 {last['total_tokens']:,} = {direction} {abs(change):.1f}%")


def summarize():
    """简要总结（供精算师内部用）"""
    stats = get_daily_stats(7)
    stats = [s for s in stats if s["sessions"] > 0]
    if not stats:
        print("今日尚无 token 数据")
        return

    today = stats[-1]
    print(f"📊 今日: {today['sessions']} session · {today['input_tokens']+today['output_tokens']:,} token · ${today['cost']:.4f}")

    if len(stats) >= 2:
        recent = stats[:-1]
        avg = sum(s["input_tokens"] + s["output_tokens"] for s in recent) / len(recent)
        today_total = today["input_tokens"] + today["output_tokens"]
        ratio = today_total / avg * 100 if avg > 0 else 100
        direction = "↑ 高于" if ratio > 110 else ("↓ 低于" if ratio < 90 else "≈ 持平")
        # 峰值
        peak = max(stats, key=lambda x: x["cost"])
        total_cost = sum(s["cost"] for s in stats)
        print(f"趋势: 今日 {direction} 近{len(recent)}日均值 ({ratio:.0f}%)")
        print(f"期间峰值: {peak['date']} ${peak['cost']:.4f} (占总量 {peak['cost']/total_cost*100:.0f}%)")
        print(f"日均成本: ${total_cost/len(stats):.4f}")


def alert_check(threshold=3.0):
    """检查今日成本是否超过日均的 threshold 倍"""
    stats = get_daily_stats(8)
    stats = [s for s in stats if s["sessions"] > 0]
    if not stats:
        print("✅ 无历史数据，跳过告警")
        return
    today = stats[-1]
    if len(stats) < 2:
        print(f"📊 仅有今日数据: ${today['cost']:.4f} (数据不足无法比对)")
        return
    recent = stats[:-1]
    avg_cost = sum(s["cost"] for s in recent) / len(recent)
    if avg_cost > 0 and today["cost"] > avg_cost * threshold:
        print(f"⚠️ **Token 成本告警**")
        print(f"├ 今日: **${today['cost']:.4f}**")
        print(f"├ 近{len(recent)}日均: ${avg_cost:.4f}")
        print(f"├ 倍率: {today['cost']/avg_cost:.1f}x")
        print(f"└ 建议: 检查今日异常会话")
    elif today["cost"] == 0:
        print(f"📊 今日尚无 token 消耗数据")
    else:
        print(f"✅ 正常 — 今日 ${today['cost']:.4f} / 日均 ${avg_cost:.4f} ({today['cost']/avg_cost:.1f}x)")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="对话精算师 Token 趋势追踪")
    parser.add_argument("--view", action="store_true", help="查看趋势")
    parser.add_argument("--summary", action="store_true", help="简要总结")
    parser.add_argument("--alert", nargs="?", const=3.0, type=float, default=None,
                        help="检查今日成本是否超过日均 N 倍 (默认 3)")
    parser.add_argument("--cross-profile", action="store_true",
                        help="跨 profile 汇总趋势")
    parser.add_argument("--top-peaks", nargs="?", const=5, type=int, default=None,
                        help="显示 Top-N 最贵日")
    parser.add_argument("--days", type=int, default=7, help="查看天数")
    args = parser.parse_args()

    if args.view:
        view_trend(args.days)
    elif args.summary:
        summarize()
    elif args.alert is not None:
        alert_check(args.alert)
    elif args.cross_profile:
        PROFILES_DIR = Path.home() / ".hermes" / "profiles"
        all_profiles = {"default": STATE_DB}
        if PROFILES_DIR.exists():
            for p in PROFILES_DIR.iterdir():
                db = p / "state.db"
                if db.exists():
                    all_profiles[p.name] = db
        print(f"📊 **跨 Profile 趋势 ({len(all_profiles)} profiles)**\n")
        total_cost_all = 0
        for name, db_path in sorted(all_profiles.items()):
            try:
                conn = sqlite3.connect(str(db_path))
                cur = conn.cursor()
                cur.execute("SELECT SUM(estimated_cost_usd), SUM(input_tokens) FROM sessions")
                r = cur.fetchone()
                cost = r[0] or 0
                inp = r[1] or 0
                total_cost_all += cost
                if cost > 0 or inp > 0:
                    print(f"├ {name}: ${cost:.4f} | {inp:,} token")
                conn.close()
            except Exception:
                pass
        print(f"\n└ **合计**: ${total_cost_all:.4f}")
    elif args.top_peaks is not None:
        conn = safe_connect()
        if not conn:
            print("❌ 无法连接数据库")
            sys.exit(1)
        cur = conn.cursor()
        cur.execute("""
            SELECT DATE(datetime(started_at, 'unixepoch')) as day,
                   ROUND(SUM(estimated_cost_usd), 4) as total_cost,
                   COUNT(*) as sessions,
                   ROUND(AVG(estimated_cost_usd), 4) as avg_cost
            FROM sessions WHERE estimated_cost_usd > 0
            GROUP BY day ORDER BY total_cost DESC LIMIT ?
        """, (args.top_peaks,))
        peaks = cur.fetchall()
        cur.execute("SELECT SUM(estimated_cost_usd) FROM sessions")
        total = cur.fetchone()[0] or 0
        conn.close()
        print(f"📊 **Top-{args.top_peaks} 最贵日** (总成本 ${total:.4f})\n")
        print(f"| 排名 | 日期 | 成本 | 占比 | Sessions | 单均 |")
        print(f"|------|------|------|------|----------|------|")
        for i, (day, cost, sessions, avg) in enumerate(peaks, 1):
            pct = cost / total * 100 if total > 0 else 0
            print(f"| {i} | {day} | ${cost:.4f} | {pct:.0f}% | {sessions} | ${avg:.4f} |")
        if peaks:
            print(f"\n**峰值日聚焦**: {peaks[0][0]} = ${peaks[0][1]:.4f} ({peaks[0][1]/total*100:.0f}% 全量)")
    else:
        result = record_today()
        if result:
            print(f"✅ Token 趋势已记录: {result['date']} | {result['sessions']} session | ${result['cost']:.4f}")
        else:
            print(f"⏭️ 今日无数据，跳过记录")
