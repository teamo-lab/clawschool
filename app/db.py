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

    for col, typedef in [
        ("generated_skills_json", "TEXT"),
        ("generated_skills_status", "TEXT NOT NULL DEFAULT ''"),
        ("generated_skills_error", "TEXT"),
        ("generated_skills_scope", "TEXT"),
        ("generated_skills_updated_at", "TEXT"),
        ("started_at", "TEXT"),
    ]:
        try:
            conn.execute(f"ALTER TABLE tests ADD COLUMN {col} {typedef}")
        except Exception:
            pass

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

    # 验证码表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS verification_codes (
            phone TEXT NOT NULL,
            code TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (phone, code)
        )
    """)

    # Waitlist 表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS waitlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            platform TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_waitlist_phone ON waitlist(phone)")

    # 分享邀请表（分享成绩免费升级）
    conn.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sharer_token TEXT NOT NULL,
            referee_token TEXT,
            referee_name TEXT,
            status TEXT NOT NULL DEFAULT 'shared',
            created_at TEXT NOT NULL,
            completed_at TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_referrals_sharer ON referrals(sharer_token)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_referrals_referee ON referrals(referee_token)")

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
