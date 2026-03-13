"""微信 JS-SDK 签名模块 — access_token / jsapi_ticket / signature"""

import hashlib
import json
import logging
import os
import random
import string
import time
import urllib.request

logger = logging.getLogger("clawschool.wechat_jssdk")

WX_APPID = os.environ.get("WX_JS_APPID", "wx0fbf1bd51f218408")
WX_APPSECRET = os.environ.get("WX_JS_APPSECRET", "3b8832f23ef90cf96b1ff12a6c393bb3")

# 内存缓存（单进程 uvicorn 足够）
_token_cache = {"token": "", "expires_at": 0}
_ticket_cache = {"ticket": "", "expires_at": 0}


def _get_access_token():
    """获取 access_token，带缓存"""
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"]:
        return _token_cache["token"]

    url = (
        "https://api.weixin.qq.com/cgi-bin/token"
        "?grant_type=client_credential"
        "&appid={}&secret={}".format(WX_APPID, WX_APPSECRET)
    )
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        if "access_token" not in data:
            logger.error("获取 access_token 失败: %s", data)
            return None
        _token_cache["token"] = data["access_token"]
        # 提前 300 秒过期，避免边界竞争
        _token_cache["expires_at"] = now + data.get("expires_in", 7200) - 300
        logger.info("access_token 已刷新，有效期 %ss", data.get("expires_in"))
        return _token_cache["token"]
    except Exception as e:
        logger.error("请求 access_token 异常: %s", e)
        return None


def _get_jsapi_ticket():
    """获取 jsapi_ticket，带缓存"""
    now = time.time()
    if _ticket_cache["ticket"] and now < _ticket_cache["expires_at"]:
        return _ticket_cache["ticket"]

    token = _get_access_token()
    if not token:
        return None

    url = (
        "https://api.weixin.qq.com/cgi-bin/ticket/getticket"
        "?access_token={}&type=jsapi".format(token)
    )
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        if data.get("errcode") != 0:
            logger.error("获取 jsapi_ticket 失败: %s", data)
            return None
        _ticket_cache["ticket"] = data["ticket"]
        _ticket_cache["expires_at"] = now + data.get("expires_in", 7200) - 300
        logger.info("jsapi_ticket 已刷新")
        return _ticket_cache["ticket"]
    except Exception as e:
        logger.error("请求 jsapi_ticket 异常: %s", e)
        return None


def get_wx_signature_data(page_url):
    """生成微信 JS-SDK 签名数据

    Args:
        page_url: 当前页面 URL（不含 hash）

    Returns:
        dict with appId, timestamp, nonceStr, signature; or None on failure
    """
    ticket = _get_jsapi_ticket()
    if not ticket:
        return None

    timestamp = str(int(time.time()))
    nonce_str = "".join(random.choices(string.ascii_letters + string.digits, k=16))

    # 签名算法：按 key 字典序拼接后 SHA1
    sign_str = "jsapi_ticket={}&noncestr={}&timestamp={}&url={}".format(
        ticket, nonce_str, timestamp, page_url
    )
    signature = hashlib.sha1(sign_str.encode("utf-8")).hexdigest()

    return {
        "appId": WX_APPID,
        "timestamp": int(timestamp),
        "nonceStr": nonce_str,
        "signature": signature,
    }
