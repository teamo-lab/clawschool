import sqlite3
import os
from pathlib import Path

def _db_dir() -> Path:
    return Path(os.environ.get("CLAWSCHOOL_DATA_DIR", "/opt/clawschool/data"))

def get_db() -> sqlite3.Connection:
    db_dir = _db_dir()
    db_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_dir / "clawschool.db"))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tests (
            token TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'waiting',
            model TEXT,
            score INTEGER,
            title TEXT,
            test_time TEXT,
            detail TEXT,
            submission TEXT,
            retest_submission TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tests_score ON tests(score DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tests_name ON tests(name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tests_status ON tests(status)")

    # 用户表（手机号登录）
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            phone TEXT PRIMARY KEY,
            created_at TEXT NOT NULL
        )
    """)

    # Token 绑定表（用户 - 测试关联）
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_tokens (
            phone TEXT NOT NULL,
            token TEXT NOT NULL,
            bound_at TEXT NOT NULL,
            PRIMARY KEY (phone, token)
        )
    """)

    # 支付订单表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            order_id TEXT PRIMARY KEY,
            phone TEXT NOT NULL DEFAULT '',
            token TEXT NOT NULL,
            amount INTEGER NOT NULL DEFAULT 9900,
            plan_type TEXT NOT NULL DEFAULT 'basic',
            channel TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'pending',
            trade_no TEXT,
            created_at TEXT NOT NULL,
            confirmed_at TEXT,
            paid_at TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_payments_phone ON payments(phone)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_payments_token ON payments(token)")

    # 兼容旧表：增量添加新列（已有 DB 不会重建表）
    for col, typedef in [
        ("plan_type", "TEXT NOT NULL DEFAULT 'basic'"),
        ("channel", "TEXT NOT NULL DEFAULT ''"),
        ("trade_no", "TEXT"),
        ("paid_at", "TEXT"),
    ]:
        try:
            conn.execute(f"ALTER TABLE payments ADD COLUMN {col} {typedef}")
        except Exception:
            pass  # 列已存在

    # trade_no 索引放在 ALTER TABLE 之后，确保列已存在
    conn.execute("CREATE INDEX IF NOT EXISTS idx_payments_trade_no ON payments(trade_no)")

    conn.commit()
    conn.close()
