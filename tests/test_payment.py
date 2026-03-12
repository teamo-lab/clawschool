"""支付模块 — 订单创建 + 回调通知 + 状态查询 + confirm 兼容（mock + 集成测试）。"""

import json
from unittest.mock import patch, MagicMock

import pytest
from tests.conftest import submit_test, integration_submit


class TestPaymentCreate:
    """创建支付订单。"""

    def test_missing_token(self, client):
        r = client.post("/api/payment/create", json={"plan_type": "basic", "channel": "alipay_h5"})
        assert r.status_code == 400

    def test_invalid_channel(self, client):
        d = submit_test(client)
        r = client.post("/api/payment/create", json={
            "token": d["token"], "plan_type": "basic", "channel": "invalid"
        })
        assert r.status_code == 400

    def test_wechat_h5_blocked(self, client):
        d = submit_test(client)
        r = client.post("/api/payment/create", json={
            "token": d["token"], "plan_type": "basic", "channel": "wechat_h5"
        })
        assert r.status_code == 400
        assert "审核" in r.json()["detail"]

    def test_alipay_h5_success(self, client):
        d = submit_test(client)
        mock_payment_info = {"pay_url": "https://openapi.alipay.com/..."}
        with patch.object(
            __import__("app.main", fromlist=["alipay_pay"]).alipay_pay,
            "create_h5_order",
            return_value=mock_payment_info,
        ):
            r = client.post("/api/payment/create", json={
                "token": d["token"], "plan_type": "basic", "channel": "alipay_h5"
            })
            assert r.status_code == 200
            data = r.json()
            assert data["success"] is True
            assert data["order_id"].startswith("PAY")
            assert data["amount"] == 19
            assert data["plan_type"] == "basic"

    def test_premium_amount(self, client):
        d = submit_test(client)
        with patch.object(
            __import__("app.main", fromlist=["alipay_pay"]).alipay_pay,
            "create_h5_order",
            return_value={"pay_url": "https://..."},
        ):
            r = client.post("/api/payment/create", json={
                "token": d["token"], "plan_type": "premium", "channel": "alipay_h5"
            })
            assert r.status_code == 200
            assert r.json()["amount"] == 99

    def test_wechat_native_success(self, client):
        d = submit_test(client)
        with patch.object(
            __import__("app.main", fromlist=["wechat_pay"]).wechat_pay,
            "create_native_order",
            return_value={"code_url": "weixin://wxpay/..."},
        ):
            r = client.post("/api/payment/create", json={
                "token": d["token"], "plan_type": "basic", "channel": "wechat_native"
            })
            assert r.status_code == 200
            assert r.json()["channel"] == "wechat_native"

    def test_order_stored_in_db(self, client):
        d = submit_test(client)
        with patch.object(
            __import__("app.main", fromlist=["alipay_pay"]).alipay_pay,
            "create_h5_order",
            return_value={"pay_url": "https://..."},
        ):
            r = client.post("/api/payment/create", json={
                "token": d["token"], "plan_type": "basic", "channel": "alipay_h5"
            })
        order_id = r.json()["order_id"]
        from app.db import get_db
        db = get_db()
        try:
            row = db.execute("SELECT * FROM payments WHERE order_id=?", (order_id,)).fetchone()
        finally:
            db.close()
        assert row is not None
        assert row["status"] == "pending"


class TestPaymentStatus:
    """支付状态查询。"""

    def test_not_found(self, client):
        r = client.get("/api/payment/status/PAYnonexistent")
        assert r.status_code == 404

    def test_pending_status(self, client):
        d = submit_test(client)
        with patch.object(
            __import__("app.main", fromlist=["alipay_pay"]).alipay_pay,
            "create_h5_order",
            return_value={"pay_url": "https://..."},
        ):
            cr = client.post("/api/payment/create", json={
                "token": d["token"], "plan_type": "basic", "channel": "alipay_h5"
            })
        order_id = cr.json()["order_id"]
        r = client.get(f"/api/payment/status/{order_id}")
        assert r.status_code == 200
        assert r.json()["status"] == "pending"


class TestPaymentConfirm:
    """兼容旧版"我已支付"按钮。"""

    def test_confirm_without_real_payment(self, client):
        d = submit_test(client)
        with patch.object(
            __import__("app.main", fromlist=["alipay_pay"]).alipay_pay,
            "create_h5_order",
            return_value={"pay_url": "https://..."},
        ):
            cr = client.post("/api/payment/create", json={
                "token": d["token"], "plan_type": "basic", "channel": "alipay_h5"
            })
        order_id = cr.json()["order_id"]
        r = client.post("/api/payment/confirm", json={"order_id": order_id})
        assert r.status_code == 200
        assert r.json()["paid"] is False  # 未真实支付

    def test_confirm_by_token(self, client):
        d = submit_test(client)
        r = client.post("/api/payment/confirm", json={"token": d["token"]})
        assert r.status_code == 200
        # 没有订单，paid=False
        assert r.json()["paid"] is False

    def test_confirm_missing_both(self, client):
        r = client.post("/api/payment/confirm", json={})
        assert r.status_code == 400


class TestAlipayCallback:
    """支付宝回调通知。"""

    def test_alipay_callback_updates_status(self, client):
        d = submit_test(client)
        # 先创建订单
        from app.db import get_db
        db = get_db()
        try:
            db.execute(
                "INSERT INTO payments (order_id, phone, token, amount, plan_type, channel, status, created_at) VALUES (?, '', ?, 19, 'basic', 'alipay_h5', 'pending', '2026-01-01')",
                ("PAYtest123", d["token"]),
            )
            db.commit()
        finally:
            db.close()

        # 模拟支付宝回调
        with patch.object(
            __import__("app.main", fromlist=["alipay_pay"]).alipay_pay,
            "verify_callback",
            return_value=True,
        ):
            r = client.post("/api/payment/alipay/notify", data={
                "trade_status": "TRADE_SUCCESS",
                "out_trade_no": "PAYtest123",
                "trade_no": "2026031222001400001",
            })
        assert r.status_code == 200
        assert r.text == "success"

        # 验证状态更新
        db = get_db()
        try:
            row = db.execute("SELECT status, trade_no FROM payments WHERE order_id='PAYtest123'").fetchone()
        finally:
            db.close()
        assert row["status"] == "paid"
        assert row["trade_no"] == "2026031222001400001"

    def test_alipay_callback_verify_fail(self, client):
        with patch.object(
            __import__("app.main", fromlist=["alipay_pay"]).alipay_pay,
            "verify_callback",
            return_value=False,
        ):
            r = client.post("/api/payment/alipay/notify", data={
                "trade_status": "TRADE_SUCCESS",
                "out_trade_no": "PAYtest123",
                "trade_no": "fake",
            })
        assert r.text == "fail"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 集成测试 — 命中 HK 真实服务器
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@pytest.mark.integration
class TestPaymentCreateIntegration:
    """创建支付订单 — 真实服务器（不触发真实支付渠道）。"""

    def test_missing_token_returns_400(self, http):
        r = http.post("/api/payment/create", json={"plan_type": "basic", "channel": "alipay_h5"})
        assert r.status_code == 400

    def test_invalid_channel_returns_400(self, http):
        d = integration_submit(http)
        r = http.post("/api/payment/create", json={
            "token": d["token"], "plan_type": "basic", "channel": "invalid_channel"
        })
        assert r.status_code == 400

    def test_wechat_h5_blocked(self, http):
        d = integration_submit(http)
        r = http.post("/api/payment/create", json={
            "token": d["token"], "plan_type": "basic", "channel": "wechat_h5"
        })
        assert r.status_code == 400
        assert "审核" in r.json()["detail"]

    def test_nonexistent_token_returns_error(self, http):
        r = http.post("/api/payment/create", json={
            "token": "nonexist9", "plan_type": "basic", "channel": "alipay_h5"
        })
        # 不存在的 token 应报错
        assert r.status_code in (400, 404)


@pytest.mark.integration
class TestPaymentStatusIntegration:
    """支付状态查询 — 真实服务器。"""

    def test_nonexistent_order_returns_404(self, http):
        r = http.get("/api/payment/status/PAYnonexistent999")
        assert r.status_code == 404


@pytest.mark.integration
class TestPaymentConfirmIntegration:
    """confirm 兼容 — 真实服务器。"""

    def test_confirm_missing_both_returns_400(self, http):
        r = http.post("/api/payment/confirm", json={})
        assert r.status_code == 400

    def test_confirm_by_token_no_order(self, http):
        d = integration_submit(http)
        r = http.post("/api/payment/confirm", json={"token": d["token"]})
        assert r.status_code == 200
        assert r.json()["paid"] is False
