"""微信 JS-SDK 签名服务"""

import hashlib
import logging
import random
import string
import time
import urllib.request
import json
from typing import Optional

logger = logging.getLogger(__name__)

# 简易内存缓存（生产环境建议使用 Redis）
_cache: dict = {}


def _get_cache(key: str) -> Optional[str]:
    """获取缓存，检查是否过期"""
    if key in _cache:
        value, expire_at = _cache[key]
        if time.time() < expire_at:
            return value
        del _cache[key]
    return None


def _set_cache(key: str, value: str, ttl: int = 7000):
    """设置缓存，ttl 单位秒（access_token 有效期 7200 秒，提前 200 秒刷新）"""
    _cache[key] = (value, time.time() + ttl)


def get_access_token(app_id: str, app_secret: str) -> Optional[str]:
    """获取微信公众号 access_token（带缓存）"""
    if not app_id or not app_secret:
        logger.warning("微信公众号 AppID 或 AppSecret 未配置")
        return None

    cache_key = f"wx_access_token:{app_id}"
    cached = _get_cache(cache_key)
    if cached:
        return cached

    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        if "access_token" in data:
            token = data["access_token"]
            expires_in = data.get("expires_in", 7200)
            _set_cache(cache_key, token, expires_in - 200)
            return token
        else:
            logger.error(f"获取 access_token 失败: {data}")
            return None
    except Exception as e:
        logger.error(f"获取 access_token 异常: {e}")
        return None


def get_jsapi_ticket(app_id: str, app_secret: str) -> Optional[str]:
    """获取 jsapi_ticket（带缓存）"""
    cache_key = f"wx_jsapi_ticket:{app_id}"
    cached = _get_cache(cache_key)
    if cached:
        return cached

    access_token = get_access_token(app_id, app_secret)
    if not access_token:
        return None

    url = f"https://api.weixin.qq.com/cgi-bin/ticket/getticket?access_token={access_token}&type=jsapi"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        if data.get("errcode") == 0 and "ticket" in data:
            ticket = data["ticket"]
            expires_in = data.get("expires_in", 7200)
            _set_cache(cache_key, ticket, expires_in - 200)
            return ticket
        else:
            logger.error(f"获取 jsapi_ticket 失败: {data}")
            return None
    except Exception as e:
        logger.error(f"获取 jsapi_ticket 异常: {e}")
        return None


def generate_signature(app_id: str, app_secret: str, url: str) -> Optional[dict]:
    """
    生成 JS-SDK 签名配置

    返回格式：
    {
        "appId": "wx...",
        "timestamp": 1234567890,
        "nonceStr": "xxxxx",
        "signature": "xxxxx"
    }
    """
    ticket = get_jsapi_ticket(app_id, app_secret)
    if not ticket:
        return None

    timestamp = int(time.time())
    nonce_str = "".join(random.choices(string.ascii_letters + string.digits, k=16))

    # 按字典序拼接签名字符串
    sign_str = f"jsapi_ticket={ticket}&noncestr={nonce_str}&timestamp={timestamp}&url={url}"
    signature = hashlib.sha1(sign_str.encode("utf-8")).hexdigest()

    return {
        "appId": app_id,
        "timestamp": timestamp,
        "nonceStr": nonce_str,
        "signature": signature,
    }
