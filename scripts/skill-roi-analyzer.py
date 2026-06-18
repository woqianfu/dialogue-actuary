#!/usr/bin/env python3
"""
Per-Skill ROI Analyzer — 按技能归因成本，找出最贵和最便宜的 skill
检测每个 skill 在 system prompt 中贡献了多少 token，花了多少钱
"""
import sqlite3, re, sys
from pathlib import Path
from datetime import datetime, timezone

DB = Path.home() / ".hermes" / "state.db"


def main():
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 获取所有含 system_prompt 的 session
    cur.execute("""
        SELECT id, system_prompt, source, model, input_tokens, output_tokens,
               cache_read_tokens, estimated_cost_usd, started_at, title
        FROM sessions
        WHERE system_prompt IS NOT NULL AND system_prompt != ''
          AND started_at >= ?
        ORDER BY started_at DESC
        LIMIT 200
    """, (datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp(),))
    sessions = cur.fetchall()

    # 从 system_prompt 中提取 skill 名称
    skill_sessions = {}  # skill_name -> list of (cost, tokens, session_id)

    for s in sessions:
        sp = s["system_prompt"] or ""
        cost = s["estimated_cost_usd"] or 0
        tokens = (s["input_tokens"] or 0) + (s["output_tokens"] or 0)

        # 从 SKILL.md 路径中提取 skill 名
        skill_matches = re.findall(r'skills/([^/]+/[^/\s]+?)/SKILL\.md', sp)
        for skill in set(skill_matches):
            if skill == "hermes/hermes-token-saver":  # 排除自身
                continue
            if skill not in skill_sessions:
                skill_sessions[skill] = {"cost": 0, "tokens": 0, "sessions": 0, "loaded": 0}
            skill_sessions[skill]["cost"] += cost
            skill_sessions[skill]["tokens"] += tokens
            skill_sessions[skill]["sessions"] += 1
            skill_sessions[skill]["loaded"] += 1

    conn.close()

    if not skill_sessions:
        print("📊 **Per-Skill ROI**: 今日无 system_prompt 数据（或今日开始不久）")
        sys.exit(0)

    total_cost = sum(v["cost"] for v in skill_sessions.values())

    # 排序
    sorted_skills = sorted(skill_sessions.items(), key=lambda x: -x[1]["cost"])

    print("📊 **Per-Skill ROI 分析**\n")

    print(f"**今日涉及 Skill**: {len(sorted_skills)} 个 | 总成本: ${total_cost:.4f}\n")

    print(f"| 排名 | Skill | 加载次数 | 分摊成本 | 占比 |")
    print(f"|------|-------|---------|---------|------|")
    for i, (name, data) in enumerate(sorted_skills[:15], 1):
        pct = data["cost"] / total_cost * 100 if total_cost > 0 else 0
        flag = " 🔴" if pct > 20 else (" 🟡" if pct > 10 else "")
        short = name.split("/")[-1] if "/" in name else name
        print(f"| {i} | {short[:25]} | {data['loaded']} | ${data['cost']:.4f} | {pct:.1f}%{flag} |")

    print(f"\n**最贵 Skill Top 3:**")
    for name, data in sorted_skills[:3]:
        short = name.split("/")[-1] if "/" in name else name
        pct = data["cost"] / total_cost * 100 if total_cost > 0 else 0
        print(f"├ ${data['cost']:.4f} ({pct:.1f}%) | {short} | 加载 {data['loaded']} 次")

    print(f"\n**零成本 Skill（加载了但没花多少钱）:**")
    cheap = [(n, d) for n, d in sorted_skills if d["cost"] < 0.01 and d["loaded"] > 0]
    for name, data in cheap[:5]:
        short = name.split("/")[-1] if "/" in name else name
        print(f"├ {short} — 加载 {data['loaded']} 次, 成本 ${data['cost']:.4f}")


if __name__ == "__main__":
    main()
