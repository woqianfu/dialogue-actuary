# Hermes state.db Schema

> 对话精算师所有脚本查询的 token 数据来源。所有 token 统计字段由 Hermes 原生写入，零额外开销。

## sessions 表（每个对话一行）

```sql
CREATE TABLE sessions (
    id                  TEXT PRIMARY KEY,          -- 形如 'weixin_xxx' / 'cli_xxx' / 'cron_xxx'
    source              TEXT NOT NULL,             -- 'weixin', 'cli', 'cron', 'tui', 'subagent'
    user_id             TEXT,
    model               TEXT,                      -- 'deepseek-v4-flash'
    model_config        TEXT,
    system_prompt       TEXT,
    parent_session_id   TEXT REFERENCES sessions(id),
    started_at          REAL NOT NULL,             -- Unix 时间戳
    ended_at            REAL,
    end_reason          TEXT,
    message_count       INTEGER DEFAULT 0,
    tool_call_count     INTEGER DEFAULT 0,
    input_tokens        INTEGER DEFAULT 0,         -- 输入 token（不含缓存命中）
    output_tokens       INTEGER DEFAULT 0,         -- 输出 token
    cache_read_tokens   INTEGER DEFAULT 0,         -- 缓存命中读取
    cache_write_tokens  INTEGER DEFAULT 0,         -- 缓存写入
    reasoning_tokens    INTEGER DEFAULT 0,         -- 扩展思考 token
    cwd                 TEXT,
    billing_provider    TEXT,                      -- 'deepseek'
    billing_base_url    TEXT,
    billing_mode        TEXT,
    estimated_cost_usd  REAL,                      -- Hermes 计算成本
    actual_cost_usd     REAL,                      -- API 实际成本
    cost_status         TEXT,
    cost_source         TEXT,
    pricing_version     TEXT,
    title               TEXT,                      -- 对话标题
    api_call_count      INTEGER DEFAULT 0,
    handoff_state       TEXT,
    handoff_platform    TEXT,
    handoff_error       TEXT,
    rewind_count        INTEGER NOT NULL DEFAULT 0,
    archived            INTEGER NOT NULL DEFAULT 0
);
```

## messages 表（每条消息一行）

```sql
CREATE TABLE messages (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id          TEXT NOT NULL REFERENCES sessions(id),
    role                TEXT NOT NULL,             -- 'user', 'assistant', 'tool'
    content             TEXT,
    tool_call_id        TEXT,
    tool_calls          TEXT,                      -- JSON
    tool_name           TEXT,
    timestamp           REAL NOT NULL,
    token_count         INTEGER,
    finish_reason       TEXT,
    reasoning           TEXT,
    reasoning_content   TEXT,
    reasoning_details   TEXT,
    codex_reasoning_items   TEXT,
    codex_message_items     TEXT,
    platform_message_id     TEXT,
    observed            INTEGER DEFAULT 0,
    active              INTEGER NOT NULL DEFAULT 1
);
```

## 索引

```sql
CREATE INDEX idx_sessions_source     ON sessions(source);
CREATE INDEX idx_sessions_source_id  ON sessions(source, id);
CREATE INDEX idx_sessions_parent     ON sessions(parent_session_id);
CREATE INDEX idx_sessions_started    ON sessions(started_at DESC);
```

## 多 profile 路径

```
~/.hermes/state.db                     ← default profile
~/.hermes/profiles/<name>/state.db     ← named profile
```

## 脚本 resolve_db()

```python
def resolve_db():
    profile = os.environ.get("HERMES_PROFILE") or os.environ.get("HERMES_ACTIVE_PROFILE")
    if profile and (PROFILES_DIR / profile / "state.db").exists():
        return PROFILES_DIR / profile / "state.db"
    return STATE_DB
```

## 关键字段速查

| 字段 | 用途 | 常见值 |
|------|------|--------|
| source | 分类统计 | weixin, cli, cron, tui, subagent |
| input_tokens | 输入成本 | 数百~数十万 |
| output_tokens | 输出成本 | 数百~数万 |
| cache_read_tokens | 缓存效率（常占95%+） | 数百万~数亿 |
| estimated_cost_usd | 美元成本 | $0.0000~$16.00 |
| title | 会话标识 | 对话标题或'设备心跳' |
| started_at | 时间筛选 | Unix float |
