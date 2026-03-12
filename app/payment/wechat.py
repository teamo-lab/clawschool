"""微信支付 V3 — Native（PC扫码）+ H5（移动端，待域名审核）"""

import base64
import json
import logging
import time
import uuid

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .config import PaymentConfig

logger = logging.getLogger(__name__)

API_BASE = "https://api.mch.weixin.qq.com"


class WechatPayClient:
    def __init__(self, config: PaymentConfig):
        self.mch_id = config.WECHAT_MCH_ID
        self.app_id = config.WECHAT_APP_ID
        self.api_v3_key = config.WECHAT_API_V3_KEY
        self.serial_no = config.WECHAT_CERT_SERIAL_NO
        self.notify_url = config.WECHAT_NOTIFY_URL
        pem = config.wechat_private_key()
        self._private_key = (
            serialization.load_pem_private_key(pem.encode(), password=None) if pem else None
        )

    @property
    def available(self) -> bool:
        return self._private_key is not None and bool(self.mch_id)

    # ── 签名 & 请求 ──

    def _sign(self, message: str) -> str:
        sig = self._private_key.sign(
            message.encode(),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return base64.b64encode(sig).decode()

    def _build_auth(self, method: str, url_path: str, body: str = "") -> str:
        ts = str(int(time.time()))
        nonce = uuid.uuid4().hex
        msg = f"{method}\n{url_path}\n{ts}\n{nonce}\n{body}\n"
        sig = self._sign(msg)
        return (
            f'WECHATPAY2-SHA256-RSA2048 mchid="{self.mch_id}",'
            f'nonce_str="{nonce}",timestamp="{ts}",'
            f'serial_no="{self.serial_no}",signature="{sig}"'
        )

    def _post(self, path: str, payload: dict) -> dict:
        body = json.dumps(payload, ensure_ascii=False)
        auth = self._build_auth("POST", path, body)
        resp = requests.post(
            API_BASE + path,
            data=body.encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": auth,
            },
            timeout=10,
        )
        if resp.status_code in (200, 204):
            return resp.json() if resp.content else {}
        logger.error("微信支付请求失败: %s %s", resp.status_code, resp.text)
        raise RuntimeError(f"微信支付请求失败: {resp.status_code} {resp.text[:200]}")

    # ── 下单 ──

    def create_native_order(self, order_id: str, amount_fen: int, description: str) -> dict:
        """PC扫码支付 — 返回 code_url（用于生成二维码）"""
        if not self.available:
            raise RuntimeError("微信支付未配置")
        data = self._post("/v3/pay/transactions/native", {
            "appid": self.app_id,
            "mchid": self.mch_id,
            "description": description,
            "out_trade_no": order_id,
            "notify_url": self.notify_url,
            "amount": {"total": amount_fen, "currency": "CNY"},
        })
        return {"code_url": data["code_url"]}

    def create_h5_order(self, order_id: str, amount_fen: int, description: str,
                        client_ip: str) -> dict:
        """H5支付 — 返回 h5_url（重定向到微信支付页面）。需 floatai.cn H5 域名审核通过。"""
        if not self.available:
            raise RuntimeError("微信支付未配置")
        data = self._post("/v3/pay/transactions/h5", {
            "appid": self.app_id,
            "mchid": self.mch_id,
            "description": description,
            "out_trade_no": order_id,
            "notify_url": self.notify_url,
            "amount": {"total": amount_fen, "currency": "CNY"},
            "scene_info": {
                "payer_client_ip": client_ip,
                "h5_info": {"type": "Wap"},
            },
        })
        return {"h5_url": data["h5_url"]}

    # ── 回调 ──

    def decrypt_callback(self, body: bytes) -> dict:
        """解密微信支付回调通知中的 resource 字段"""
        data = json.loads(body)
        resource = data["resource"]
        nonce = resource["nonce"].encode()
        ciphertext = base64.b64decode(resource["ciphertext"])
        aad = resource.get("associated_data", "").encode()
        aes = AESGCM(self.api_v3_key.encode())
        plaintext = aes.decrypt(nonce, ciphertext, aad)
        return json.loads(plaintext)
