"""HMAC 签名的无状态 session token"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import base64
from typing import Optional

SECRET = os.environ.get("SESSION_SECRET", "lobster-iq-dev-secret-2026")
SESSION_TTL_SECONDS = 30 * 60  # 30 分钟


def create_session_token(question_ids: list) -> tuple:
    """创建签名 session token，返回 (session_id, expires_at_ms)"""
    now = int(time.time())
    expires_at = now + SESSION_TTL_SECONDS

    payload = {
        "question_ids": question_ids,
        "created_at": now,
        "expires_at": expires_at,
    }

    data = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    sig = _sign(data)
    session_id = f"{data}.{sig}"

    return session_id, expires_at * 1000  # 返回毫秒时间戳


def verify_session_token(session_id: str) -> Optional[dict]:
    """验证 session token，返回 payload 或 None"""
    parts = session_id.split(".")
    if len(parts) != 2:
        return None

    data, sig = parts
    if _sign(data) != sig:
        return None

    try:
        # 补齐 base64 padding
        padding = 4 - len(data) % 4
        if padding != 4:
            data += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(data))
    except Exception:
        return None

    if time.time() > payload.get("expires_at", 0):
        return None

    return payload


def _sign(data: str) -> str:
    return hmac.new(
        SECRET.encode(), data.encode(), hashlib.sha256
    ).hexdigest()[:32]
