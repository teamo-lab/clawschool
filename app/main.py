"""龙虾学校后端 — FastAPI + Jinja2 SSR + SQLite"""

import hashlib
import hmac
import json
import logging
import os
import string
import random
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .db import get_db, init_db
from .scorer import score_submission, merge_retest, get_title, raw_to_iq, SCORERS, TOTAL_SCORE
from .og_image import generate_og_image
from .questions import QUESTIONS
from .repair import generate_repair_skill, generate_premium_repair_skill, ADVANCED_QIDS, BASIC_QIDS
from .payment import PaymentConfig, WechatPayClient, AlipayClient

logger = logging.getLogger("clawschool")

BASE_DIR = Path(__file__).resolve().parent.parent
SKILL_TEMPLATE = BASE_DIR / "public" / "SKILL.md"
DIAGNOSE_SKILL_TEMPLATE = BASE_DIR / "public" / "DIAGNOSE-SKILL.md"
DOMAIN = os.environ.get("CLAWSCHOOL_DOMAIN", "clawschool.teamolab.com")

app = FastAPI(title="龙虾学校", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
QUESTION_IDS = [q["id"] for q in QUESTIONS]

pay_config = PaymentConfig()
wechat_pay = WechatPayClient(pay_config)
alipay_pay = AlipayClient(pay_config)

VALID_CHANNELS = {"wechat_native", "wechat_h5", "alipay_pc", "alipay_h5"}

@app.on_event("startup")
def startup():
    init_db()

# ─── 工具函数 ───

def _gen_token(length: int = 8) -> str:
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choices(chars, k=length))

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _public_base_url() -> str:
    """对外公开 URL 前缀：线上默认 https，本地开发域名默认 http。"""
    raw_domain = (DOMAIN or "").strip().rstrip("/")
    if not raw_domain:
        return ""
    if raw_domain.startswith("http://") or raw_domain.startswith("https://"):
        return raw_domain

    host = raw_domain.split(":", 1)[0].lower()
    scheme = "http" if host in {"127.0.0.1", "localhost", "0.0.0.0"} else "https"
    return f"{scheme}://{raw_domain}"

def _render_public_skill(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    base_url = _public_base_url()
    # 兼容历史模板中的硬编码域名，也支持后续引入占位符。
    content = content.replace("https://clawschool.teamolab.com", base_url)
    content = content.replace("http://clawschool.teamolab.com", base_url)
    content = content.replace("{{BASE_URL}}", base_url)
    return content

def _get_rank(score: int, token: str):
    """获取指定 token 在排行榜中的排名"""
    db = get_db()
    try:
        row = db.execute(
            "SELECT COUNT(*) as rank FROM tests WHERE status='done' AND (score > ? OR (score = ? AND token < ?))",
            (score, score, token)
        ).fetchone()
        return (row["rank"] + 1) if row else None
    finally:
        db.close()

# ─── API 接口 ───

@app.post("/api/token")
async def create_token(request: Request):
    body = await request.json()
    name = (body.get("name") or "").strip()
    if not name or len(name) > 20:
        raise HTTPException(400, "龙虾名字需要 1-20 个字符")

    token = _gen_token()
    now = _now_iso()
    db = get_db()
    try:
        # 确保 token 唯一
        while db.execute("SELECT 1 FROM tests WHERE token=?", (token,)).fetchone():
            token = _gen_token()
        db.execute(
            "INSERT INTO tests (token, name, status, created_at, updated_at) VALUES (?, ?, 'waiting', ?, ?)",
            (token, name, now, now)
        )
        db.commit()
    finally:
        db.close()

    from urllib.parse import quote
    skill_url = f"{_public_base_url()}/skill.md?token={token}&name={quote(name)}"
    return {"token": token, "name": name, "skill_url": skill_url, "created_at": now}


@app.get("/skill.md")
async def get_skill(token: str = "", name: str = ""):
    if not SKILL_TEMPLATE.exists():
        raise HTTPException(404, "SKILL.md 未配置")
    content = _render_public_skill(SKILL_TEMPLATE)
    return PlainTextResponse(content, media_type="text/markdown; charset=utf-8")


@app.get("/skills/diagnose.md")
async def get_diagnose_skill():
    if not DIAGNOSE_SKILL_TEMPLATE.exists():
        raise HTTPException(404, "DIAGNOSE-SKILL.md 未配置")
    content = _render_public_skill(DIAGNOSE_SKILL_TEMPLATE)
    return PlainTextResponse(content, media_type="text/markdown; charset=utf-8")



@app.get("/api/test/start")
async def test_start(token: str = ""):
    """下发全部题目给 bot。可选传入 token 绑定到已有记录。"""
    questions_out = []
    for q in QUESTIONS:
        questions_out.append({
            "id": q["id"],
            "title": q["title"],
            "category": q["category"],
            "instructions": q["instructions"],
            "evidence_format": q["evidence_format"],
        })
    return {
        "questionCount": len(questions_out),
        "questions": questions_out,
        "submitUrl": f"{_public_base_url()}/api/test/submit",
    }


@app.post("/api/test/submit")
async def test_submit(request: Request):
    """Bot 提交全部证据，自动评分并返回成绩。"""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "无效的 JSON")

    token = (body.get("token") or "").strip()
    lobster_name = (body.get("lobsterName") or body.get("lobster_name") or "匿名龙虾").strip()
    model = body.get("model", "unknown")
    answers = body.get("answers", {})

    # 将 answers 展开为 scorer 期望的格式（兼容两种提交方式）
    # 方式1: {"answers": {"q1": {...}, "q2": {...}}}
    # 方式2: {"q1": {...}, "q2": {...}} (旧格式，直接在顶层)
    submission = {}
    for qid in QUESTION_IDS:
        submission[qid] = answers.get(qid) or body.get(qid) or {}

    submission["token"] = token
    submission["lobster_name"] = lobster_name
    submission["model"] = model
    submission["test_time"] = body.get("test_time", _now_iso())

    # 评分
    result = score_submission(submission)
    score = result["score"]
    title = result["title"]
    detail_json = json.dumps(result["detail"], ensure_ascii=False)
    submission_json = json.dumps(submission, ensure_ascii=False)

    now = _now_iso()

    # 写入数据库
    db = get_db()
    try:
        if token:
            existing = db.execute("SELECT token, status, score, title FROM tests WHERE token=?", (token,)).fetchone()
            if existing:
                # 防止重复提交：如果已经完成，直接返回现有结果
                if existing["status"] == "done":
                    db.close()
                    return {
                        "success": True,
                        "token": token,
                        "lobsterName": lobster_name,
                        "score": existing["score"],
                        "iq": raw_to_iq(existing["score"]),
                        "title": existing["title"],
                        "rank": _get_rank(existing["score"], token),
                        "detail": result["detail"],
                        "report_url": f"https://{DOMAIN}/r/{token}",
                        "diagnoseUrl": f"/api/test/diagnose?token={token}",
                        "repairSkillUrl": f"https://{DOMAIN}/api/repair-skill/{token}",
                        "duplicate": True,  # 标记为重复提交
                    }
                db.execute("""
                    UPDATE tests SET
                        status='done', model=?, score=?, title=?, test_time=?,
                        detail=?, submission=?, updated_at=?
                    WHERE token=? AND status='waiting'
                """, (model, score, title, submission["test_time"],
                      detail_json, submission_json, now, token))
            else:
                db.execute("""
                    INSERT INTO tests (token, name, status, model, score, title, test_time,
                        detail, submission, created_at, updated_at)
                    VALUES (?, ?, 'done', ?, ?, ?, ?, ?, ?, ?, ?)
                """, (token, lobster_name, model, score, title,
                      submission["test_time"], detail_json, submission_json, now, now))
        else:
            token = _gen_token()
            db.execute("""
                INSERT INTO tests (token, name, status, model, score, title, test_time,
                    detail, submission, created_at, updated_at)
                VALUES (?, ?, 'done', ?, ?, ?, ?, ?, ?, ?, ?)
            """, (token, lobster_name, model, score, title,
                  submission["test_time"], detail_json, submission_json, now, now))
        db.commit()
    finally:
        db.close()

    rank = _get_rank(score, token)

    return {
        "success": True,
        "token": token,
        "lobsterName": lobster_name,
        "score": score,
        "iq": raw_to_iq(score),
        "title": title,
        "rank": rank,
        "detail": result["detail"],
        "report_url": f"{_public_base_url()}/r/{token}",
        "diagnoseUrl": f"/api/test/diagnose?token={token}",
        "repairSkillUrl": f"{_public_base_url()}/api/repair-skill/{token}",
    }


@app.get("/api/result/{token}")
async def get_result(token: str):
    db = get_db()
    try:
        row = db.execute("SELECT * FROM tests WHERE token=?", (token,)).fetchone()
    finally:
        db.close()
    if not row:
        raise HTTPException(404, "Token 不存在")

    data = dict(row)

    # 检查 waiting 状态的 token 是否过期（30 分钟）
    if data["status"] == "waiting" and data.get("created_at"):
        from datetime import datetime, timedelta, timezone
        try:
            created = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            if datetime.now(timezone.utc) - created > timedelta(minutes=30):
                return {"status": "expired", "name": data["name"], "message": "测试已过期，请重新开始"}
        except Exception:
            pass

    resp = {"status": data["status"], "name": data["name"], "created_at": data.get("created_at")}

    if data["status"] == "done":
        resp.update({
            "model": data["model"],
            "score": data["score"],
            "iq": raw_to_iq(data["score"]),
            "title": data["title"],
            "test_time": data["test_time"],
            "detail": json.loads(data["detail"]) if data["detail"] else {},
            "original_submission": json.loads(data["submission"]) if data["submission"] else None,
            "retest_submission": json.loads(data["retest_submission"]) if data["retest_submission"] else None,
            "rank": _get_rank(data["score"], token),
        })

    return resp


@app.get("/api/test/diagnose")
async def test_diagnose(token: str, scope: str = "full"):
    """诊断：返回答卷详情，供 agent 端分析弱项和推荐 skills。
    scope=basic 只分析基础 8 题（BASIC_QIDS），scope=full 分析全部 12 题。
    """
    db = get_db()
    try:
        row = db.execute("SELECT * FROM tests WHERE token=? AND status='done'", (token,)).fetchone()
    finally:
        db.close()
    if not row:
        raise HTTPException(404, "未找到测试结果，请先完成测试")

    if scope not in {"basic", "full"}:
        raise HTTPException(400, "scope 仅支持 basic 或 full")

    detail = json.loads(row["detail"]) if row["detail"] else {}
    submission = json.loads(row["submission"]) if row["submission"] else {}

    diagnosis_result = _build_diagnosis_result(token, row, detail, submission, scope)
    diagnosis_result["generatedSkills"] = _fetch_generated_skills(token, diagnosis_result)
    return diagnosis_result


def _build_diagnosis_result(token: str, row, detail: dict, submission: dict, scope: str) -> dict:
    if scope == "basic":
        target_qids = BASIC_QIDS
    else:
        target_qids = QUESTION_IDS

    q_index = {q["id"]: q for q in QUESTIONS}
    question_details = []
    for qid in target_qids:
        q = q_index.get(qid, {})
        d = detail.get(qid, {})
        s = submission.get(qid, {})
        question_details.append({
            "questionId": qid,
            "title": q.get("title", ""),
            "category": q.get("category", ""),
            "instructions": q.get("instructions", ""),
            "evidenceFormat": q.get("evidence_format", {}),
            "agentEvidence": s if isinstance(s, dict) else {},
            "score": d.get("score", 0),
            "maxScore": d.get("max", 10),
            "reason": d.get("reason", ""),
        })

    return {
        "token": token,
        "lobsterName": row["name"],
        "model": row["model"],
        "score": row["score"],
        "iq": raw_to_iq(row["score"]),
        "title": row["title"],
        "rank": _get_rank(row["score"], token),
        "scope": scope,
        "questionDetails": question_details,
    }


def _fetch_generated_skills(token: str, diagnosis_result: dict) -> list:
    CLAUDE_API_URL = os.environ.get("CLAUDE_API_URL", "http://49.51.47.101:8900")
    try:
        payload = json.dumps({"token": token, "diagnosis": diagnosis_result}).encode()
        req = urllib.request.Request(
            f"{CLAUDE_API_URL}/api/generate-skills",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=200) as resp:
            skills_result = json.loads(resp.read())
        return skills_result.get("skills", [])
    except Exception:
        return []


@app.get("/api/repair-skill/{token}")
async def repair_skill(token: str, plan: str = "basic"):
    """根据诊断结果生成个性化修复 SKILL.md，bot 直接执行即可自动修复+重测"""
    db = get_db()
    try:
        row = db.execute("SELECT * FROM tests WHERE token=? AND status='done'", (token,)).fetchone()
    finally:
        db.close()
    if not row:
        raise HTTPException(404, "未找到测试结果，请先完成测试")

    detail = json.loads(row["detail"]) if row["detail"] else {}
    submission = json.loads(row["submission"]) if row["submission"] else {}
    plan = (plan or "basic").strip().lower()
    if plan not in {"basic", "premium"}:
        raise HTTPException(400, "plan 仅支持 basic 或 premium")

    if plan == "basic":
        all_perfect = all(
            detail.get(qid, {}).get("score", 0) >= detail.get(qid, {}).get("max", 10)
            for qid in QUESTION_IDS
        )
        if all_perfect:
            return PlainTextResponse(
                "# 恭喜！你的 bot 已经全部满分，无需修复。\n\n当前得分：{}/{}".format(row["score"], TOTAL_SCORE),
                media_type="text/markdown; charset=utf-8",
            )

        skill_content = generate_repair_skill(
            token=token,
            lobster_name=row["name"],
            score=row["score"],
            detail=detail,
            submission=submission,
        )
    else:
        diagnosis_result = _build_diagnosis_result(token, row, detail, submission, "full")
        generated_skills = _fetch_generated_skills(token, diagnosis_result)
        skill_content = generate_premium_repair_skill(
            token=token,
            lobster_name=row["name"],
            score=row["score"],
            detail=detail,
            generated_skills=generated_skills,
        )
    return PlainTextResponse(skill_content, media_type="text/markdown; charset=utf-8")


@app.get("/api/leaderboard")
async def leaderboard(limit: int = 50, offset: int = 0):
    db = get_db()
    try:
        # 同名取最高分，使用子查询
        rows = db.execute("""
            SELECT name, model, MAX(score) as score, title, test_time, token
            FROM tests WHERE status='done'
            GROUP BY name
            ORDER BY score DESC, test_time ASC
            LIMIT ? OFFSET ?
        """, (limit, offset)).fetchall()
        total_row = db.execute(
            "SELECT COUNT(DISTINCT name) as cnt FROM tests WHERE status='done'"
        ).fetchone()
    finally:
        db.close()

    entries = []
    for i, row in enumerate(rows):
        entries.append({
            "rank": offset + i + 1,
            "name": row["name"],
            "model": row["model"],
            "score": row["score"],
            "iq": raw_to_iq(row["score"]),
            "title": row["title"],
            "test_time": row["test_time"],
        })

    return {"total": total_row["cnt"] if total_row else 0, "entries": entries}


@app.get("/api/stats")
async def stats():
    db = get_db()
    try:
        total = db.execute("SELECT COUNT(*) as cnt FROM tests WHERE status='done'").fetchone()["cnt"]
        avg = db.execute("SELECT AVG(score) as avg FROM tests WHERE status='done'").fetchone()["avg"]
        rows = db.execute("SELECT title, COUNT(*) as cnt FROM tests WHERE status='done' GROUP BY title").fetchall()
    finally:
        db.close()

    distribution = {r["title"]: r["cnt"] for r in rows}
    avg_iq = raw_to_iq(round(avg)) if avg else 0
    return {
        "total_tests": total,
        "avg_score": round(avg, 1) if avg else 0,
        "avg_iq": avg_iq,
        "title_distribution": distribution,
    }


@app.get("/api/recent")
async def recent(limit: int = 10):
    db = get_db()
    try:
        rows = db.execute("""
            SELECT token, name, score, title, model, test_time
            FROM tests WHERE status='done'
            ORDER BY updated_at DESC LIMIT ?
        """, (limit,)).fetchall()
    finally:
        db.close()
    entries = []
    for r in rows:
        e = dict(r)
        e["iq"] = raw_to_iq(e["score"])
        entries.append(e)
    return {"entries": entries}


@app.get("/api/active-count")
async def active_count():
    """返回当前正在测试中的龙虾数量（status=waiting）"""
    db = get_db()
    try:
        row = db.execute(
            "SELECT COUNT(*) as cnt FROM tests WHERE status='waiting'"
        ).fetchone()
        total = db.execute(
            "SELECT COUNT(*) as cnt FROM tests WHERE status='done'"
        ).fetchone()
    finally:
        db.close()
    return {
        "active": row["cnt"] if row else 0,
        "total_done": total["cnt"] if total else 0,
    }


@app.get("/api/og-image/{token}")
async def og_image(token: str):
    db = get_db()
    try:
        row = db.execute("SELECT * FROM tests WHERE token=? AND status='done'", (token,)).fetchone()
    finally:
        db.close()
    if not row:
        raise HTTPException(404, "未找到测试结果")

    rank = _get_rank(row["score"], token)
    path = generate_og_image(token, row["name"], row["score"], row["title"], rank)
    return FileResponse(str(path), media_type="image/png")


@app.post("/api/upgrade/basic")
async def upgrade_basic(request: Request):
    """¥19.9 基础能力升级重测。重测全 12 题，取 max(原始分, 重测分) 合并。"""
    body = await request.json()
    token = body.get("token", "").strip()
    if not token:
        raise HTTPException(400, "缺少 token")

    db = get_db()
    try:
        row = db.execute("SELECT * FROM tests WHERE token=? AND status='done'", (token,)).fetchone()
    finally:
        db.close()
    if not row:
        raise HTTPException(404, "未找到原始测试结果")

    original_detail = json.loads(row["detail"]) if row["detail"] else {}
    original_score = row["score"]
    original_title = row["title"]

    # 对提交的所有题重新评分
    all_qids = list(SCORERS.keys())
    retest_qids = []
    retest_detail = {}
    for qid in all_qids:
        q_data = body.get(qid, {})
        if isinstance(q_data, dict) and q_data:
            scorer = SCORERS[qid]
            pts, reason = scorer(q_data)
            retest_detail[qid] = {"score": pts, "max": 10, "reason": reason}
            retest_qids.append(qid)

    merged = merge_retest(original_detail, retest_detail, retest_qids)
    now = _now_iso()

    db = get_db()
    try:
        db.execute("""
            UPDATE tests SET
                score=?, title=?, detail=?, retest_submission=?, updated_at=?
            WHERE token=?
        """, (
            merged["score"], merged["title"],
            json.dumps(merged["detail"], ensure_ascii=False),
            json.dumps(body, ensure_ascii=False),
            now, token
        ))
        db.commit()
    finally:
        db.close()

    return {
        "success": True,
        "token": token,
        "retest_scores": {qid: retest_detail.get(qid, {}).get("score", 0) for qid in retest_qids},
        "new_total": merged["score"],
        "old_total": original_score,
        "new_iq": raw_to_iq(merged["score"]),
        "old_iq": raw_to_iq(original_score),
        "new_title": merged["title"],
        "old_title": original_title,
    }


# ─── 腾讯云短信 ───

SMS_SECRET_ID = os.environ.get("TC_SMS_SECRET_ID", "")
SMS_SECRET_KEY = os.environ.get("TC_SMS_SECRET_KEY", "")
SMS_SDK_APP_ID = os.environ.get("TC_SMS_SDK_APP_ID", "")
SMS_SIGN_NAME = os.environ.get("TC_SMS_SIGN_NAME", "龙虾学校")
SMS_TEMPLATE_ID = os.environ.get("TC_SMS_TEMPLATE_ID", "")


def _tc3_sign(secret_key: str, date: str, service: str, string_to_sign: str) -> str:
    """TC3-HMAC-SHA256 签名。"""
    def _hmac_sha256(key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    secret_date = _hmac_sha256(f"TC3{secret_key}".encode("utf-8"), date)
    secret_service = _hmac_sha256(secret_date, service)
    secret_signing = _hmac_sha256(secret_service, "tc3_request")
    return hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()


def _send_sms(phone: str, template_params: list[str]) -> bool:
    """调用腾讯云 SMS SendSms API 发送短信。成功返回 True，失败返回 False。"""
    if not all([SMS_SECRET_ID, SMS_SECRET_KEY, SMS_SDK_APP_ID, SMS_TEMPLATE_ID]):
        logger.warning("SMS 配置不完整，跳过发送 (phone=%s)", phone[-4:])
        return False

    service = "sms"
    host = f"{service}.tencentcloudapi.com"
    action = "SendSms"
    version = "2021-01-11"
    region = "ap-guangzhou"

    # 手机号需要 +86 前缀
    phone_e164 = f"+86{phone}" if not phone.startswith("+") else phone

    payload = {
        "SmsSdkAppId": SMS_SDK_APP_ID,
        "SignName": SMS_SIGN_NAME,
        "TemplateId": SMS_TEMPLATE_ID,
        "PhoneNumberSet": [phone_e164],
        "TemplateParamSet": template_params,
    }
    payload_str = json.dumps(payload, separators=(",", ":"))

    timestamp = int(datetime.now(timezone.utc).timestamp())
    date = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d")

    # 构造规范请求
    hashed_payload = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
    canonical_request = (
        f"POST\n/\n\n"
        f"content-type:application/json; charset=utf-8\n"
        f"host:{host}\n\n"
        f"content-type;host\n"
        f"{hashed_payload}"
    )
    hashed_canonical = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    credential_scope = f"{date}/{service}/tc3_request"
    string_to_sign = f"TC3-HMAC-SHA256\n{timestamp}\n{credential_scope}\n{hashed_canonical}"

    signature = _tc3_sign(SMS_SECRET_KEY, date, service, string_to_sign)
    authorization = (
        f"TC3-HMAC-SHA256 Credential={SMS_SECRET_ID}/{credential_scope}, "
        f"SignedHeaders=content-type;host, Signature={signature}"
    )

    req = urllib.request.Request(
        f"https://{host}",
        data=payload_str.encode("utf-8"),
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Host": host,
            "Authorization": authorization,
            "X-TC-Action": action,
            "X-TC-Version": version,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Region": region,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
        send_status = result.get("Response", {}).get("SendStatusSet", [])
        if send_status and send_status[0].get("Code") == "Ok":
            logger.info("SMS 发送成功 (phone=%s)", phone[-4:])
            return True
        error = result.get("Response", {}).get("Error", {})
        logger.warning("SMS 发送失败: %s (phone=%s)", error or send_status, phone[-4:])
        return False
    except Exception as exc:
        logger.warning("SMS 发送异常: %s (phone=%s)", exc, phone[-4:])
        return False


# ─── 登录 & 支付 API ───

MVP_VERIFY_CODE = "888888"
CODE_EXPIRY_SECONDS = 300  # 5 分钟

def _gen_verify_code() -> str:
    return "".join(random.choices(string.digits, k=6))

@app.post("/api/login/send-code")
async def send_code(request: Request):
    body = await request.json()
    phone = (body.get("phone") or "").strip()
    if not phone or len(phone) != 11 or not phone.isdigit():
        raise HTTPException(400, "请输入 11 位手机号")

    code = _gen_verify_code()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=CODE_EXPIRY_SECONDS)
    now_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    expires_iso = expires_at.strftime("%Y-%m-%dT%H:%M:%SZ")

    db = get_db()
    try:
        # 清理该手机号旧验证码
        db.execute("DELETE FROM verification_codes WHERE phone=?", (phone,))
        db.execute(
            "INSERT INTO verification_codes (phone, code, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (phone, code, now_iso, expires_iso)
        )
        db.commit()
    finally:
        db.close()

    # 发送真实短信（失败不阻塞，万能验证码 888888 始终可用）
    sms_sent = _send_sms(phone, [code])
    return {"success": True, "expires_in": CODE_EXPIRY_SECONDS, "sms_sent": sms_sent}


@app.post("/api/login")
async def login(request: Request):
    body = await request.json()
    phone = (body.get("phone") or "").strip()
    code = (body.get("code") or "").strip()
    token = (body.get("token") or "").strip()

    if not phone or len(phone) != 11:
        raise HTTPException(400, "手机号格式不正确")

    # 验证码校验：万能码 888888 或数据库中未过期的验证码
    if code != MVP_VERIFY_CODE:
        now_iso = _now_iso()
        db = get_db()
        try:
            # 先检查验证码是否存在
            row = db.execute(
                "SELECT code, expires_at, used FROM verification_codes WHERE phone=? AND code=?",
                (phone, code)
            ).fetchone()
            if not row:
                raise HTTPException(400, "验证码不正确")
            if row["used"] == 1:
                raise HTTPException(400, "验证码已使用，请重新获取")
            if row["expires_at"] <= now_iso:
                raise HTTPException(400, "验证码已过期，请重新获取")
            db.execute(
                "UPDATE verification_codes SET used=1 WHERE phone=? AND code=?",
                (phone, code)
            )
            db.commit()
        finally:
            db.close()

    now = _now_iso()
    db = get_db()
    try:
        # 创建或忽略用户
        db.execute(
            "INSERT OR IGNORE INTO users (phone, created_at) VALUES (?, ?)",
            (phone, now)
        )
        # 绑定 token（如果提供）
        if token:
            db.execute(
                "INSERT OR IGNORE INTO user_tokens (phone, token, bound_at) VALUES (?, ?, ?)",
                (phone, token, now)
            )
        db.commit()
    finally:
        db.close()

    return {"success": True, "phone": phone}


@app.post("/api/payment/create")
async def payment_create(request: Request):
    """创建支付订单并发起真实支付。
    channel: wechat_native | wechat_h5 | alipay_pc | alipay_h5
    """
    body = await request.json()
    phone = (body.get("phone") or "").strip()
    token = (body.get("token") or "").strip()
    plan_type = (body.get("plan_type") or "basic").strip()
    channel = (body.get("channel") or "").strip()

    if not token:
        raise HTTPException(400, "缺少 token")
    if plan_type not in {"basic", "premium"}:
        raise HTTPException(400, "plan_type 仅支持 basic 或 premium")
    if channel not in VALID_CHANNELS:
        raise HTTPException(400, f"不支持的支付渠道，可选: {', '.join(sorted(VALID_CHANNELS))}")

    # 微信 H5 域名审核中，暂不开放
    if channel == "wechat_h5":
        raise HTTPException(400, "微信 H5 支付域名审核中，请使用支付宝 H5 或微信扫码支付")

    # token 必须存在，避免脏订单写入
    db = get_db()
    try:
        token_row = db.execute("SELECT 1 FROM tests WHERE token=?", (token,)).fetchone()
    finally:
        db.close()
    if not token_row:
        raise HTTPException(404, "token 不存在，请先创建测试记录")

    # TODO: 测试期间使用小额，正式上线改回 1990 / 9900
    amount = 19 if plan_type == "basic" else 99
    description = "龙虾学校 - 基础能力升级" if plan_type == "basic" else "龙虾学校 - 高级能力订阅"
    order_id = "PAY" + _gen_token(12)
    now = _now_iso()

    # 调用支付渠道
    try:
        if channel == "wechat_native":
            payment_info = wechat_pay.create_native_order(order_id, amount, description)
        elif channel == "wechat_h5":
            client_ip = request.client.host if request.client else "127.0.0.1"
            payment_info = wechat_pay.create_h5_order(order_id, amount, description, client_ip)
        elif channel == "alipay_pc":
            # 构造带 token 和 paid 参数的 return_url
            alipay_return_url = f"{_public_base_url()}/me/{token}?paid=premium" if plan_type == "premium" else f"{_public_base_url()}/wait/{token}?paid=basic"
            payment_info = alipay_pay.create_pc_order(order_id, amount, description, alipay_return_url)
        elif channel == "alipay_h5":
            alipay_return_url = f"{_public_base_url()}/me/{token}?paid=premium" if plan_type == "premium" else f"{_public_base_url()}/wait/{token}?paid=basic"
            payment_info = alipay_pay.create_h5_order(order_id, amount, description, alipay_return_url)
    except RuntimeError as e:
        raise HTTPException(500, str(e))

    # 支付渠道返回成功后再写库，避免失败时留下 pending 脏数据
    db = get_db()
    try:
        db.execute(
            """INSERT INTO payments (order_id, phone, token, amount, plan_type, channel, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)""",
            (order_id, phone, token, amount, plan_type, channel, now),
        )
        db.commit()
    finally:
        db.close()

    return {
        "success": True,
        "order_id": order_id,
        "channel": channel,
        "amount": amount,
        "plan_type": plan_type,
        "payment_info": payment_info,
    }


@app.post("/api/payment/wechat/notify")
async def wechat_notify(request: Request):
    """微信支付异步回调"""
    body = await request.body()
    try:
        result = wechat_pay.decrypt_callback(body)
    except Exception:
        return JSONResponse({"code": "FAIL", "message": "解密失败"}, status_code=400)

    out_trade_no = result.get("out_trade_no", "")
    trade_state = result.get("trade_state", "")
    transaction_id = result.get("transaction_id", "")

    if trade_state == "SUCCESS":
        now = _now_iso()
        db = get_db()
        try:
            db.execute(
                "UPDATE payments SET status='paid', trade_no=?, paid_at=?, confirmed_at=? WHERE order_id=? AND status='pending'",
                (transaction_id, now, now, out_trade_no),
            )
            db.commit()
        finally:
            db.close()

    return JSONResponse({"code": "SUCCESS", "message": "OK"})


@app.post("/api/payment/alipay/notify")
async def alipay_notify(request: Request):
    """支付宝异步回调"""
    form = await request.form()
    data = dict(form)

    if not alipay_pay.verify_callback(data):
        return PlainTextResponse("fail")

    trade_status = data.get("trade_status", "")
    out_trade_no = data.get("out_trade_no", "")
    trade_no = data.get("trade_no", "")

    if trade_status in ("TRADE_SUCCESS", "TRADE_FINISHED"):
        now = _now_iso()
        db = get_db()
        try:
            db.execute(
                "UPDATE payments SET status='paid', trade_no=?, paid_at=?, confirmed_at=? WHERE order_id=? AND status='pending'",
                (trade_no, now, now, out_trade_no),
            )
            db.commit()
        finally:
            db.close()

    return PlainTextResponse("success")


@app.get("/api/payment/alipay/return")
async def alipay_return(request: Request):
    """支付宝同步返回（用户支付后跳转回来）"""
    from fastapi.responses import RedirectResponse
    out_trade_no = request.query_params.get("out_trade_no", "")
    if out_trade_no:
        db = get_db()
        try:
            row = db.execute("SELECT token, plan_type FROM payments WHERE order_id=?", (out_trade_no,)).fetchone()
        finally:
            db.close()
        if row:
            if row["plan_type"] == "premium":
                return RedirectResponse(url=f"/me/{row['token']}?paid=premium", status_code=302)
            else:
                return RedirectResponse(url=f"/wait/{row['token']}?paid=basic", status_code=302)
    return RedirectResponse(url="/", status_code=302)


@app.get("/api/payment/status/{order_id}")
async def payment_status(order_id: str):
    """前端轮询支付状态，超过 10 分钟未支付自动过期"""
    db = get_db()
    try:
        row = db.execute(
            "SELECT order_id, token, amount, plan_type, channel, status, paid_at, created_at FROM payments WHERE order_id=?",
            (order_id,),
        ).fetchone()
        if not row:
            raise HTTPException(404, "订单不存在")

        # 检查是否过期：pending 状态且超过 10 分钟
        if row["status"] == "pending" and row["created_at"]:
            from datetime import datetime, timedelta, timezone
            try:
                created = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
                if datetime.now(timezone.utc) - created > timedelta(minutes=10):
                    db.execute("UPDATE payments SET status='expired' WHERE order_id=? AND status='pending'", (order_id,))
                    db.commit()
                    result = dict(row)
                    result["status"] = "expired"
                    return result
            except Exception:
                pass
    finally:
        db.close()
    return dict(row)


@app.post("/api/payment/confirm")
async def payment_confirm(request: Request):
    """向后兼容：旧版前端"我已支付"按钮调用。真实支付到账后由回调自动更新状态。"""
    body = await request.json()
    order_id = (body.get("order_id") or "").strip()
    token = (body.get("token") or "").strip()
    plan_type = (body.get("plan_type") or "").strip()

    if not order_id and not token:
        raise HTTPException(400, "缺少订单号或 token")
    if plan_type and plan_type not in {"basic", "premium"}:
        raise HTTPException(400, "plan_type 仅支持 basic 或 premium")

    # 查询是否已真实支付
    db = get_db()
    try:
        if order_id:
            row = db.execute("SELECT status FROM payments WHERE order_id=?", (order_id,)).fetchone()
        else:
            if plan_type:
                row = db.execute(
                    "SELECT status FROM payments WHERE token=? AND plan_type=? ORDER BY datetime(created_at) DESC LIMIT 1",
                    (token, plan_type),
                ).fetchone()
            else:
                row = db.execute(
                    "SELECT status FROM payments WHERE token=? ORDER BY datetime(created_at) DESC LIMIT 1",
                    (token,),
                ).fetchone()
    finally:
        db.close()

    paid = row["status"] == "paid" if row else False
    return {"success": True, "paid": paid}


# ─── Waitlist ───

@app.post("/api/waitlist")
async def join_waitlist(request: Request):
    body = await request.json()
    phone = (body.get("phone") or "").strip()
    platform = (body.get("platform") or "").strip()
    if not phone or len(phone) != 11 or not phone.isdigit():
        raise HTTPException(400, "手机号格式不正确")
    if platform not in ("pc", "mobile"):
        raise HTTPException(400, "platform 必须为 pc 或 mobile")
    db = get_db()
    try:
        db.execute(
            "INSERT INTO waitlist (phone, platform) VALUES (?, ?)",
            (phone, platform),
        )
        db.commit()
    finally:
        db.close()
    return {"success": True, "message": "已加入等待列表"}


# ─── SSR 页面路由 ───

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "domain": DOMAIN,
        "public_base_url": _public_base_url(),
    })


@app.get("/r/{token}")
async def report_page(request: Request, token: str):
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/wait/{token}", status_code=302)


@app.get("/s/{token}", response_class=HTMLResponse)
async def share_page(request: Request, token: str):
    db = get_db()
    try:
        row = db.execute("SELECT * FROM tests WHERE token=?", (token,)).fetchone()
    finally:
        db.close()

    if not row:
        raise HTTPException(404, "Token 不存在")

    data = dict(row)
    data["detail"] = json.loads(data["detail"]) if data["detail"] else {}
    data["rank"] = _get_rank(data["score"], token) if data["status"] == "done" else None
    data["iq"] = raw_to_iq(data["score"]) if data["status"] == "done" else 0

    return templates.TemplateResponse("share.html", {
        "request": request,
        "domain": DOMAIN,
        "public_base_url": _public_base_url(),
        "data": data,
        "token": token,
    })


@app.get("/wait/{token}", response_class=HTMLResponse)
async def wait_page(request: Request, token: str):
    db = get_db()
    try:
        row = db.execute("SELECT * FROM tests WHERE token=?", (token,)).fetchone()
    finally:
        db.close()

    if not row:
        raise HTTPException(404, "Token 不存在")

    data = dict(row)
    data["detail"] = json.loads(data["detail"]) if data["detail"] else {}
    data["rank"] = _get_rank(data["score"], token) if data["status"] == "done" else None

    data["iq"] = raw_to_iq(data["score"]) if data["status"] == "done" else 0

    return templates.TemplateResponse("detail.html", {
        "request": request,
        "domain": DOMAIN,
        "public_base_url": _public_base_url(),
        "data": data,
        "token": token,
        "advanced_qids": ADVANCED_QIDS, "basic_qids": BASIC_QIDS, "raw_to_iq": raw_to_iq,
    })


@app.get("/me/{token}", response_class=HTMLResponse)
async def me_page(request: Request, token: str):
    db = get_db()
    try:
        row = db.execute("SELECT * FROM tests WHERE token=?", (token,)).fetchone()
    finally:
        db.close()

    if not row:
        raise HTTPException(404, "Token 不存在")

    data = dict(row)
    data["detail"] = json.loads(data["detail"]) if data["detail"] else {}
    data["rank"] = _get_rank(data["score"], token) if data["status"] == "done" else None
    data["iq"] = raw_to_iq(data["score"]) if data["status"] == "done" else 0

    # 查看是否有付费订单
    db = get_db()
    try:
        payment = db.execute(
            "SELECT status, confirmed_at FROM payments WHERE token=? AND plan_type='premium' ORDER BY datetime(created_at) DESC LIMIT 1",
            (token,)
        ).fetchone()
        total_done = db.execute(
            "SELECT COUNT(*) as cnt FROM tests WHERE status='done'"
        ).fetchone()["cnt"]
    finally:
        db.close()

    payment_status = payment["status"] if payment else None
    expire_date = ""
    if payment and payment["confirmed_at"]:
        from datetime import datetime, timedelta
        try:
            confirmed = datetime.fromisoformat(payment["confirmed_at"].replace("Z", "+00:00"))
            expire = confirmed + timedelta(days=30)
            expire_date = expire.strftime("%Y-%m-%d")
        except Exception:
            expire_date = ""

    return templates.TemplateResponse("me.html", {
        "request": request,
        "domain": DOMAIN,
        "public_base_url": _public_base_url(),
        "data": data,
        "token": token,
        "payment_status": payment_status, "total_done": total_done,
        "advanced_qids": ADVANCED_QIDS, "basic_qids": BASIC_QIDS,
        "expire_date": expire_date,
    })


@app.get("/leaderboard")
async def leaderboard_page():
    """排行榜已内嵌到首页，旧链接重定向"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/#leaderboard", status_code=302)
