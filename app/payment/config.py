"""支付配置 — 从环境变量加载"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class PaymentConfig:
    # ── 微信公众号（JS-SDK 分享）──
    WECHAT_MP_APP_ID = os.environ.get("WECHAT_MP_APP_ID", "wx0fbf1bd51f218408")
    WECHAT_MP_APP_SECRET = os.environ.get("WECHAT_MP_APP_SECRET", "")

    # ── 微信支付 ──
    WECHAT_MCH_ID = os.environ.get("WECHAT_MCH_ID", "")
    WECHAT_API_V3_KEY = os.environ.get("WECHAT_API_V3_KEY", "")
    WECHAT_APP_ID = os.environ.get("WECHAT_APP_ID", "")
    WECHAT_CERT_SERIAL_NO = os.environ.get("WECHAT_CERT_SERIAL_NO", "")
    WECHAT_NOTIFY_URL = os.environ.get("WECHAT_NOTIFY_URL", "")
    _WECHAT_KEY_PATH = os.environ.get("WECHAT_KEY_PATH", "credentials/wechat/apiclient_key.pem")
    _WECHAT_CERT_PATH = os.environ.get("WECHAT_CERT_PATH", "credentials/wechat/apiclient_cert.pem")

    # ── 支付宝 ──
    ALIPAY_APP_ID = os.environ.get("ALIPAY_APP_ID", "")
    ALIPAY_NOTIFY_URL = os.environ.get("ALIPAY_NOTIFY_URL", "")
    ALIPAY_RETURN_URL = os.environ.get("ALIPAY_RETURN_URL", "")
    ALIPAY_GATEWAY = os.environ.get("ALIPAY_GATEWAY", "https://openapi.alipay.com/gateway.do")
    _ALIPAY_APP_PRIVATE_KEY_PATH = os.environ.get(
        "ALIPAY_APP_PRIVATE_KEY_PATH", "credentials/alipay/app_private_key"
    )
    _ALIPAY_PUBLIC_KEY_PATH = os.environ.get(
        "ALIPAY_PUBLIC_KEY_PATH", "credentials/alipay/public_key"
    )

    @classmethod
    def _read_file(cls, raw_path: str) -> str:
        p = Path(raw_path)
        if not p.is_absolute():
            p = BASE_DIR / p
        return p.read_text().strip() if p.exists() else ""

    @classmethod
    def wechat_private_key(cls) -> str:
        return cls._read_file(cls._WECHAT_KEY_PATH)

    @classmethod
    def alipay_app_private_key(cls) -> str:
        return cls._read_file(cls._ALIPAY_APP_PRIVATE_KEY_PATH)

    @classmethod
    def alipay_public_key(cls) -> str:
        return cls._read_file(cls._ALIPAY_PUBLIC_KEY_PATH)

    @classmethod
    def is_wechat_configured(cls) -> bool:
        return bool(cls.WECHAT_MCH_ID and cls.WECHAT_API_V3_KEY and cls.wechat_private_key())

    @classmethod
    def is_alipay_configured(cls) -> bool:
        return bool(cls.ALIPAY_APP_ID and cls.alipay_app_private_key())
