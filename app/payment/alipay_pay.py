"""支付宝 — 电脑网站支付（PC）+ 手机网站支付（H5）"""

import logging
from alipay import AliPay
from .config import PaymentConfig

logger = logging.getLogger(__name__)


def _ensure_pem(key_str: str, key_type: str = "RSA PRIVATE KEY") -> str:
    """裸 base64 密钥 → PEM 格式。已有 PEM 头则原样返回。"""
    key_str = key_str.strip()
    if key_str.startswith("-----"):
        return key_str
    header = f"-----BEGIN {key_type}-----"
    footer = f"-----END {key_type}-----"
    # 按 64 字符折行
    body = "\n".join(key_str[i:i+64] for i in range(0, len(key_str), 64))
    return f"{header}\n{body}\n{footer}"


class AlipayClient:
    def __init__(self, config: PaymentConfig):
        self.config = config
        app_private_key = _ensure_pem(config.alipay_app_private_key(), "RSA PRIVATE KEY")
        alipay_public_key = _ensure_pem(config.alipay_public_key(), "PUBLIC KEY")

        if not config.ALIPAY_APP_ID or not app_private_key:
            self._client = None
            return

        self._client = AliPay(
            appid=config.ALIPAY_APP_ID,
            app_notify_url=config.ALIPAY_NOTIFY_URL,
            app_private_key_string=app_private_key,
            alipay_public_key_string=alipay_public_key,
            sign_type="RSA2",
            debug=False,
        )
        self._gateway = config.ALIPAY_GATEWAY

    @property
    def available(self) -> bool:
        return self._client is not None

    def create_pc_order(self, order_id: str, amount_fen: int, subject: str, return_url: str = None) -> dict:
        """电脑网站支付 — 返回完整支付 URL（前端跳转）"""
        if not self._client:
            raise RuntimeError("支付宝未配置")
        amount_yuan = f"{amount_fen / 100:.2f}"
        order_string = self._client.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=amount_yuan,
            subject=subject,
            return_url=return_url or self.config.ALIPAY_RETURN_URL,
        )
        return {"pay_url": f"{self._gateway}?{order_string}"}

    def create_h5_order(self, order_id: str, amount_fen: int, subject: str, return_url: str = None) -> dict:
        """手机网站支付 — 返回完整支付 URL（H5 跳转）"""
        if not self._client:
            raise RuntimeError("支付宝未配置")
        amount_yuan = f"{amount_fen / 100:.2f}"
        order_string = self._client.api_alipay_trade_wap_pay(
            out_trade_no=order_id,
            total_amount=amount_yuan,
            subject=subject,
            return_url=return_url or self.config.ALIPAY_RETURN_URL,
        )
        return {"pay_url": f"{self._gateway}?{order_string}"}

    def verify_callback(self, data: dict) -> bool:
        """验证支付宝异步通知签名"""
        if not self._client:
            return False
        signature = data.pop("sign", "")
        return self._client.verify(data, signature)
