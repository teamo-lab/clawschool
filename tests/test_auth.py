"""注册登录模块 — 验证码生成/过期/复用 + 手机号登录 + token 绑定。"""

import time
from unittest.mock import patch

import pytest
from tests.conftest import submit_test


class TestSendCode:
    """发送验证码。"""

    def test_success(self, client):
        r = client.post("/api/login/send-code", json={"phone": "13800138000"})
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["expires_in"] == 300

    def test_invalid_phone_short(self, client):
        r = client.post("/api/login/send-code", json={"phone": "1380013"})
        assert r.status_code == 400

    def test_invalid_phone_letters(self, client):
        r = client.post("/api/login/send-code", json={"phone": "1380013abcd"})
        assert r.status_code == 400

    def test_empty_phone(self, client):
        r = client.post("/api/login/send-code", json={"phone": ""})
        assert r.status_code == 400

    def test_no_phone_field(self, client):
        r = client.post("/api/login/send-code", json={})
        assert r.status_code == 400

    def test_code_stored_in_db(self, client):
        client.post("/api/login/send-code", json={"phone": "13800138000"})
        from app.db import get_db
        db = get_db()
        try:
            row = db.execute(
                "SELECT code, used FROM verification_codes WHERE phone='13800138000'"
            ).fetchone()
        finally:
            db.close()
        assert row is not None
        assert len(row["code"]) == 6
        assert row["used"] == 0

    def test_resend_replaces_old_code(self, client):
        client.post("/api/login/send-code", json={"phone": "13800138000"})
        client.post("/api/login/send-code", json={"phone": "13800138000"})
        from app.db import get_db
        db = get_db()
        try:
            rows = db.execute(
                "SELECT code FROM verification_codes WHERE phone='13800138000' AND used=0"
            ).fetchall()
        finally:
            db.close()
        # 旧码被清理，只保留最新的
        assert len(rows) == 1


class TestLogin:
    """手机号登录。"""

    def test_mvp_code_888888(self, client):
        r = client.post("/api/login", json={"phone": "13800138000", "code": "888888"})
        assert r.status_code == 200
        assert r.json()["success"] is True

    def test_wrong_code_rejected(self, client):
        client.post("/api/login/send-code", json={"phone": "13800138000"})
        r = client.post("/api/login", json={"phone": "13800138000", "code": "000000"})
        assert r.status_code == 400

    def test_real_code_accepted(self, client):
        client.post("/api/login/send-code", json={"phone": "13900139000"})
        from app.db import get_db
        db = get_db()
        try:
            row = db.execute(
                "SELECT code FROM verification_codes WHERE phone='13900139000' AND used=0"
            ).fetchone()
        finally:
            db.close()
        code = row["code"]
        r = client.post("/api/login", json={"phone": "13900139000", "code": code})
        assert r.status_code == 200
        assert r.json()["success"] is True

    def test_used_code_rejected(self, client):
        client.post("/api/login/send-code", json={"phone": "13900139000"})
        from app.db import get_db
        db = get_db()
        try:
            row = db.execute(
                "SELECT code FROM verification_codes WHERE phone='13900139000' AND used=0"
            ).fetchone()
        finally:
            db.close()
        code = row["code"]
        # 第一次登录
        client.post("/api/login", json={"phone": "13900139000", "code": code})
        # 第二次用同一验证码
        r = client.post("/api/login", json={"phone": "13900139000", "code": code})
        assert r.status_code == 400

    def test_expired_code_rejected(self, client):
        client.post("/api/login/send-code", json={"phone": "13900139000"})
        from app.db import get_db
        db = get_db()
        try:
            # 手动把过期时间改到过去
            db.execute(
                "UPDATE verification_codes SET expires_at='2020-01-01T00:00:00Z' WHERE phone='13900139000'"
            )
            db.commit()
            row = db.execute(
                "SELECT code FROM verification_codes WHERE phone='13900139000'"
            ).fetchone()
        finally:
            db.close()
        code = row["code"]
        r = client.post("/api/login", json={"phone": "13900139000", "code": code})
        assert r.status_code == 400

    def test_invalid_phone_format(self, client):
        r = client.post("/api/login", json={"phone": "123", "code": "888888"})
        assert r.status_code == 400


class TestTokenBinding:
    """登录时绑定 token。"""

    def test_login_binds_token(self, client):
        d = submit_test(client)
        client.post("/api/login", json={"phone": "13800138000", "code": "888888", "token": d["token"]})
        from app.db import get_db
        db = get_db()
        try:
            row = db.execute(
                "SELECT * FROM user_tokens WHERE phone='13800138000' AND token=?", (d["token"],)
            ).fetchone()
        finally:
            db.close()
        assert row is not None

    def test_login_creates_user(self, client):
        client.post("/api/login", json={"phone": "13800138000", "code": "888888"})
        from app.db import get_db
        db = get_db()
        try:
            row = db.execute("SELECT * FROM users WHERE phone='13800138000'").fetchone()
        finally:
            db.close()
        assert row is not None

    def test_login_without_token_ok(self, client):
        r = client.post("/api/login", json={"phone": "13800138000", "code": "888888"})
        assert r.status_code == 200
