#!/usr/bin/env python3
"""
Cache Anomaly Detector — 对话精算师 v2.0
检测缓存率异常低的 session，定位缓存失效原因。

用法：
  python3 cache-anomaly-detector.py                  ← 最近 7 天
  python3 cache-anomaly-detector.py --days 30        ← 最近 N 天
  python3 cache-anomaly-detector.py --threshold 80   ← 缓存率低于 X% 视为异常（默认 50）
  python3 cache-anomaly-detector.py --json           ← JSON 输出
"""

import sqlite3, json, sys, os
from pathlib import Path
from datetime import datetime, timezone, timedelta

STATE_DB = Path.home() / ".hermes" / "state.db"


def fmt_time(ts):
    return datetime.fromtimestamp(ts).strftime("%m-%d %H:%M") if ts else "-"


def detect(days=7, threshold=50, output_json=False):
    conn = sqlite3.connect(str(STATE_DB))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cur.execute("""
        SELECT id, source, title, started_at, message_count,
               input_tokens, output_tokens, cache_read_tokens,
               estimated_cost_usd, actual_cost_usd
        FROM sessions
        WHERE started_at >= ?
        ORDER BY started_at DESC
    """, (cutoff.timestamp(),))

    anomalies = []
    ok_count = 0
    for r in cur.fetchall():
        inp = r["input_tokens"] or 0
        out = r["output_tokens"] or 0
        cache = r["cache_read_tokens"] or 0
        total = inp + out + cache
        cost = r["estimated_cost_usd"] or r["actual_cost_usd"] or 0

        if total == 0:
            continue

        cache_pct = round(cache / total * 100, 1)

        if cache_pct < threshold:
            # Determine likely cause
            cause = ""
            if r["message_count"] is not None and r["message_count"] <= 5 and cache == 0:
                cause = "新鲜 session（系统 prompt 首次加载，缓存尚未建立）"
            elif cache == 0:
                cause = "缓存完全失效（系统 prompt 变更 / skill 安装 / 配置更新）"
            elif cache_pct < 20:
                cause = "缓存几乎失效（prompt 显著变更，少量缓存残留）"
            elif cache_pct < threshold:
                cause = f"缓存部分失效（仅 {cache_pct}%，疑似部分 prompt 变更）"

            anomalies.append({
                "id": r["id"],
                "source": r["source"],
                "title": (r["title"] or "?")[:50],
                "time": fmt_time(r["started_at"]),
                "msg_count": r["message_count"],
                "input_tokens": inp,
                "output_tokens": out,
                "cache_read": cache,
                "cache_pct": cache_pct,
                "cost": round(cost, 4),
                "cause": cause,
            })
        else:
            ok_count += 1

    conn.close()

    if output_json:
        print(json.dumps({
            "total_checked": len(anomalies) + ok_count,
            "anomalies_count": len(anomalies),
            "ok_count": ok_count,
            "anomalies": anomalies,
        }, ensure_ascii=False, indent=2))
        return

    total = len(anomalies) + ok_count
    print(f"📊 **缓存异常检测** — 近 {days} 天 (缓存率 < {threshold}%)")
    print(f"├ 检查: {total} session | 异常: {len(anomalies)} | 正常: {ok_count}")
    if anomalies:
        total_cost = sum(a["cost"] for a in anomalies)
        print(f"└ 异常 session 总成本: **${total_cost:.4f}**\n")
        for a in anomalies:
            src_prefix = "[cron] " if a['source'] == "cron" else ""
            print(f"⚠️ {src_prefix}{a['source']} `{a['id'][:16]}...` | {a['time']}")
            print(f"├ 标题: {a['title']}")
            print(f"├ 消息: {a['msg_count']} | 输入: {a['input_tokens']:,} | 输出: {a['output_tokens']:,}")
            print(f"├ 缓存: {a['cache_read']:,} ({a['cache_pct']}%) | 成本: **${a['cost']:.4f}**")
            print(f"└ 原因: {a['cause']}\n")
        total_input = sum(a["input_tokens"] for a in anomalies)
        print(f"**潜在浪费**: 若这些 session 有正常缓存（96-99%），输入可降至 ~{round(total_input * (1 - 0.97)):,} token / ${total_cost:.4f} → ~${total_cost/10:.4f}")
    else:
        print("\n✅ 无异常 — 所有 session 缓存率正常")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--threshold", type=float, default=50)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    detect(days=args.days, threshold=args.threshold, output_json=args.json)
