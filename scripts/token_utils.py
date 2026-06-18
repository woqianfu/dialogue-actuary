"""
Token Utils — 精算师团队共享工具模块
所有脚本应优先从此模块导入而非各自实现
"""
import sqlite3, os
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal

HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
STATE_DB = HERMES_HOME / "state.db"
PROFILES_DIR = HERMES_HOME / "profiles"

# Token 定价常量（deepseek-v4-flash）
INPUT_COST_PER_M = Decimal("0.14")
OUTPUT_COST_PER_M = Decimal("0.28")
CACHE_READ_COST_PER_M = Decimal("0.003")
CACHE_WRITE_COST_PER_M = Decimal("0.014")


def resolve_db(profile_hint: str = "") -> Path:
    """统一 profile 感知的 DB 路径解析"""
    profile = (profile_hint or
               os.environ.get("HERMES_PROFILE") or
               os.environ.get("HERMES_ACTIVE_PROFILE"))
    if profile and (PROFILES_DIR / profile / "state.db").exists():
        return PROFILES_DIR / profile / "state.db"
    return STATE_DB


def safe_connect(db_path=None):
    """统一的安全数据库连接，失败时返回 None 而非崩溃"""
    path = str(resolve_db() if db_path is None else db_path)
    if not Path(path).exists():
        return None
    try:
        conn = sqlite3.connect(path)
        conn.execute("SELECT 1 FROM sessions LIMIT 1")
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.OperationalError:
        return None


def fmt_num(n):
    """统一数字格式化：1K / 1.5M / 2.1B"""
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def fmt_time(ts):
    """统一时间戳格式化（本地时区安全）"""
    if not ts:
        return "-"
    return datetime.fromtimestamp(ts).strftime("%m-%d %H:%M")


def today_range():
    """返回今天的 UTC 时间戳范围 (today_start, now)"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return today_start.timestamp(), now.timestamp()


def estimate_token_cost(inp=0, out=0, cache_r=0, cache_w=0):
    """按 deepseek-v4-flash 费率估算成本"""
    return float(
        Decimal(inp) * INPUT_COST_PER_M / 1_000_000
        + Decimal(out) * OUTPUT_COST_PER_M / 1_000_000
        + Decimal(cache_r) * CACHE_READ_COST_PER_M / 1_000_000
        + Decimal(cache_w) * CACHE_WRITE_COST_PER_M / 1_000_000
    )


def cache_rate(inp=0, out=0, cache=0):
    """计算缓存率，避免除零"""
    total = inp + out + cache
    return cache / total * 100 if total > 0 else 0.0
