"""龙虾学校后端 — FastAPI + Jinja2 SSR + SQLite"""

import json
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
from .repair import generate_repair_skill, ADVANCED_QIDS, BASIC_QIDS
from .payment import PaymentConfig, WechatPayClient, AlipayClient

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
    skill_url = f"https://{DOMAIN}/skill.md?token={token}&name={quote(name)}"
    return {"token": token, "name": name, "skill_url": skill_url, "created_at": now}


@app.get("/skill.md")
async def get_skill(token: str = "", name: str = ""):
    if not SKILL_TEMPLATE.exists():
        raise HTTPException(404, "SKILL.md 未配置")
    content = SKILL_TEMPLATE.read_text(encoding="utf-8")
    return PlainTextResponse(content, media_type="text/markdown; charset=utf-8")


@app.get("/skills/diagnose.md")
async def get_diagnose_skill():
    if not DIAGNOSE_SKILL_TEMPLATE.exists():
        raise HTTPException(404, "DIAGNOSE-SKILL.md 未配置")
    content = DIAGNOSE_SKILL_TEMPLATE.read_text(encoding="utf-8")
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
        "submitUrl": f"https://{DOMAIN}/api/test/submit",
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
            existing = db.execute("SELECT token FROM tests WHERE token=?", (token,)).fetchone()
            if existing:
                db.execute("""
                    UPDATE tests SET
                        status='done', model=?, score=?, title=?, test_time=?,
                        detail=?, submission=?, updated_at=?
                    WHERE token=?
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
        "report_url": f"https://{DOMAIN}/r/{token}",
        "diagnoseUrl": f"/api/test/diagnose?token={token}",
        "repairSkillUrl": f"https://{DOMAIN}/api/repair-skill/{token}",
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
    resp = {"status": data["status"], "name": data["name"]}

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

    detail = json.loads(row["detail"]) if row["detail"] else {}
    submission = json.loads(row["submission"]) if row["submission"] else {}

    # 根据 scope 筛选题目范围
    if scope == "basic":
        target_qids = BASIC_QIDS
    else:
        target_qids = QUESTION_IDS

    # 构建题目索引
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

    diagnosis_result = {
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

    # 异步调用美国 Claude Code API 生成 skills（非阻塞，失败不影响诊断结果）
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
        diagnosis_result["generatedSkills"] = skills_result.get("skills", [])
    except Exception:
        diagnosis_result["generatedSkills"] = []

    return diagnosis_result


@app.get("/api/repair-skill/{token}")
async def repair_skill(token: str):
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

    # 检查是否全部满分
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

    # TODO: 接入腾讯云短信 API 发送真实验证码
    # MVP 阶段不发真实短信，万能验证码 888888 始终可用
    return {"success": True, "expires_in": CODE_EXPIRY_SECONDS}


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
            row = db.execute(
                "SELECT code FROM verification_codes WHERE phone=? AND code=? AND expires_at>? AND used=0",
                (phone, code, now_iso)
            ).fetchone()
            if not row:
                raise HTTPException(400, "验证码不正确或已过期")
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
    if channel not in VALID_CHANNELS:
        raise HTTPException(400, f"不支持的支付渠道，可选: {', '.join(sorted(VALID_CHANNELS))}")

    # 微信 H5 域名审核中，暂不开放
    if channel == "wechat_h5":
        raise HTTPException(400, "微信 H5 支付域名审核中，请使用支付宝 H5 或微信扫码支付")

    # TODO: 测试期间使用小额，正式上线改回 1990 / 9900
    amount = 19 if plan_type == "basic" else 99
    description = "龙虾学校 - 基础能力升级" if plan_type == "basic" else "龙虾学校 - 高级能力订阅"
    order_id = "PAY" + _gen_token(12)
    now = _now_iso()

    # 写入数据库
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

    # 调用支付渠道
    try:
        if channel == "wechat_native":
            payment_info = wechat_pay.create_native_order(order_id, amount, description)
        elif channel == "wechat_h5":
            client_ip = request.client.host if request.client else "127.0.0.1"
            payment_info = wechat_pay.create_h5_order(order_id, amount, description, client_ip)
        elif channel == "alipay_pc":
            payment_info = alipay_pay.create_pc_order(order_id, amount, description)
        elif channel == "alipay_h5":
            payment_info = alipay_pay.create_h5_order(order_id, amount, description)
    except RuntimeError as e:
        raise HTTPException(500, str(e))

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
    """前端轮询支付状态"""
    db = get_db()
    try:
        row = db.execute(
            "SELECT order_id, token, amount, plan_type, channel, status, paid_at FROM payments WHERE order_id=?",
            (order_id,),
        ).fetchone()
    finally:
        db.close()
    if not row:
        raise HTTPException(404, "订单不存在")
    return dict(row)


@app.post("/api/payment/confirm")
async def payment_confirm(request: Request):
    """向后兼容：旧版前端"我已支付"按钮调用。真实支付到账后由回调自动更新状态。"""
    body = await request.json()
    order_id = (body.get("order_id") or "").strip()
    token = (body.get("token") or "").strip()

    if not order_id and not token:
        raise HTTPException(400, "缺少订单号或 token")

    # 查询是否已真实支付
    db = get_db()
    try:
        if order_id:
            row = db.execute("SELECT status FROM payments WHERE order_id=?", (order_id,)).fetchone()
        else:
            row = db.execute(
                "SELECT status FROM payments WHERE token=? ORDER BY created_at DESC LIMIT 1",
                (token,),
            ).fetchone()
    finally:
        db.close()

    paid = row["status"] == "paid" if row else False
    return {"success": True, "paid": paid}


# ─── SSR 页面路由 ───

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "domain": DOMAIN})


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
        "request": request, "domain": DOMAIN, "data": data, "token": token,
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
        "request": request, "domain": DOMAIN, "data": data, "token": token,
        "advanced_qids": ADVANCED_QIDS, "basic_qids": BASIC_QIDS,
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
            "SELECT status, confirmed_at FROM payments WHERE token=? ORDER BY created_at DESC LIMIT 1",
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
        "request": request, "domain": DOMAIN, "data": data, "token": token,
        "payment_status": payment_status, "total_done": total_done,
        "advanced_qids": ADVANCED_QIDS, "basic_qids": BASIC_QIDS,
        "expire_date": expire_date,
    })


@app.get("/leaderboard")
async def leaderboard_page():
    """排行榜已内嵌到首页，旧链接重定向"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/#leaderboard", status_code=302)
