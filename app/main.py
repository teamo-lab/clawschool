"""龙虾学校后端 — FastAPI + Jinja2 SSR + SQLite"""

import json
import os
import string
import random
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .db import get_db, init_db
from .scorer import score_submission, merge_retest, get_title, SCORERS
from .og_image import generate_og_image
from .questions import QUESTIONS

BASE_DIR = Path(__file__).resolve().parent.parent
SKILL_TEMPLATE = BASE_DIR / "public" / "SKILL.md"
DOMAIN = os.environ.get("CLAWSCHOOL_DOMAIN", "clawschool.teamolab.com")

app = FastAPI(title="龙虾学校", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

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
    skill_url = f"http://{DOMAIN}/skill.md?token={token}&name={quote(name)}"
    return {"token": token, "name": name, "skill_url": skill_url, "created_at": now}


@app.get("/skill.md")
async def get_skill(token: str = "", name: str = ""):
    if not SKILL_TEMPLATE.exists():
        raise HTTPException(404, "SKILL.md 未配置")
    content = SKILL_TEMPLATE.read_text(encoding="utf-8")
    return PlainTextResponse(content, media_type="text/markdown; charset=utf-8")


@app.get("/api/test/start")
async def test_start(token: str = ""):
    """下发全部 10 道题给 bot。可选传入 token 绑定到已有记录。"""
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
        "submitUrl": f"http://{DOMAIN}/api/test/submit",
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
    for qid in ["q1", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9", "q10"]:
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
        "title": title,
        "rank": rank,
        "detail": result["detail"],
        "report_url": f"http://{DOMAIN}/r/{token}",
    }


@app.post("/api/submit")
async def submit_result(request: Request):
    try:
        submission = await request.json()
    except Exception:
        raise HTTPException(400, "无效的 JSON")

    token = submission.get("token", "").strip()
    if not token:
        raise HTTPException(400, "缺少 token 字段")

    now = _now_iso()
    result = score_submission(submission)
    score = result["score"]
    title = result["title"]
    detail_json = json.dumps(result["detail"], ensure_ascii=False)
    submission_json = json.dumps(submission, ensure_ascii=False)

    db = get_db()
    try:
        existing = db.execute("SELECT token FROM tests WHERE token=?", (token,)).fetchone()
        if existing:
            db.execute("""
                UPDATE tests SET
                    status='done', model=?, score=?, title=?, test_time=?,
                    detail=?, submission=?, updated_at=?
                WHERE token=?
            """, (
                submission.get("model"),
                score, title,
                submission.get("test_time"),
                detail_json, submission_json, now,
                token
            ))
        else:
            # 自动创建记录（兼容 bot 先提交的情况）
            name = submission.get("lobster_name", "匿名龙虾")
            db.execute("""
                INSERT INTO tests (token, name, status, model, score, title, test_time,
                    detail, submission, created_at, updated_at)
                VALUES (?, ?, 'done', ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                token, name, submission.get("model"),
                score, title, submission.get("test_time"),
                detail_json, submission_json, now, now
            ))
        db.commit()
    finally:
        db.close()

    rank = _get_rank(score, token)
    return {
        "success": True,
        "token": token,
        "score": score,
        "title": title,
        "rank": rank,
        "detail": result["detail"],
        "report_url": f"http://{DOMAIN}/r/{token}",
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
            "title": data["title"],
            "test_time": data["test_time"],
            "detail": json.loads(data["detail"]) if data["detail"] else {},
            "original_submission": json.loads(data["submission"]) if data["submission"] else None,
            "retest_submission": json.loads(data["retest_submission"]) if data["retest_submission"] else None,
            "rank": _get_rank(data["score"], token),
        })

    return resp


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
    return {
        "total_tests": total,
        "avg_score": round(avg, 1) if avg else 0,
        "title_distribution": distribution,
    }


@app.get("/api/recent")
async def recent(limit: int = 10):
    db = get_db()
    try:
        rows = db.execute("""
            SELECT name, score, title, model, test_time
            FROM tests WHERE status='done'
            ORDER BY updated_at DESC LIMIT ?
        """, (limit,)).fetchall()
    finally:
        db.close()
    return {"entries": [dict(r) for r in rows]}


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


@app.post("/api/upgrade/search")
async def upgrade_search(request: Request):
    """向后兼容旧版 SKILL.md 的搜索升级端点。新版基础升级直接复用 /api/test/submit 同 token 覆盖。"""
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

    # 对提交的所有题重新评分（支持全 10 题或仅 Q5/Q10 向后兼容）
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
        "new_title": merged["title"],
        "old_title": original_title,
    }


# ─── 登录 & 支付 API ───

MVP_VERIFY_CODE = "888888"

@app.post("/api/login/send-code")
async def send_code(request: Request):
    body = await request.json()
    phone = (body.get("phone") or "").strip()
    if not phone or len(phone) != 11 or not phone.isdigit():
        raise HTTPException(400, "请输入 11 位手机号")
    # MVP: 不发真实短信，返回成功即可
    return {"success": True, "message": "验证码已发送"}


@app.post("/api/login")
async def login(request: Request):
    body = await request.json()
    phone = (body.get("phone") or "").strip()
    code = (body.get("code") or "").strip()
    token = (body.get("token") or "").strip()

    if not phone or len(phone) != 11:
        raise HTTPException(400, "手机号格式不正确")
    if code != MVP_VERIFY_CODE:
        raise HTTPException(400, "验证码不正确")

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
    body = await request.json()
    phone = (body.get("phone") or "").strip()
    token = (body.get("token") or "").strip()
    plan_type = (body.get("plan_type") or "basic").strip()

    if not token:
        raise HTTPException(400, "缺少 token")

    # plan_type: basic=1990(¥19.9), premium=9900(¥99)
    amount = 1990 if plan_type == "basic" else 9900

    order_id = "PAY" + _gen_token(12)
    now = _now_iso()

    db = get_db()
    try:
        db.execute(
            "INSERT INTO payments (order_id, phone, token, amount, status, created_at) VALUES (?, ?, ?, ?, 'pending', ?)",
            (order_id, phone, token, amount, now)
        )
        db.commit()
    finally:
        db.close()

    return {"success": True, "order_id": order_id, "amount": amount, "plan_type": plan_type}


@app.post("/api/payment/confirm")
async def payment_confirm(request: Request):
    """用户点击"我已支付"后调用。TODO: 接入真实支付系统验证。MVP 阶段前端点击即放行。"""
    body = await request.json()
    order_id = (body.get("order_id") or "").strip()
    token = (body.get("token") or "").strip()

    if not order_id and not token:
        raise HTTPException(400, "缺少订单号或 token")

    now = _now_iso()
    db = get_db()
    try:
        if order_id:
            db.execute(
                "UPDATE payments SET status='submitted', confirmed_at=? WHERE order_id=?",
                (now, order_id)
            )
        elif token:
            db.execute(
                "UPDATE payments SET status='submitted', confirmed_at=? WHERE token=? AND status='pending'",
                (now, token)
            )
        db.commit()
    finally:
        db.close()

    return {"success": True}


# ─── SSR 页面路由 ───

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "domain": DOMAIN})


@app.get("/r/{token}", response_class=HTMLResponse)
async def report_page(request: Request, token: str):
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

    return templates.TemplateResponse("report.html", {
        "request": request, "domain": DOMAIN, "data": data, "token": token,
    })


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

    return templates.TemplateResponse("wait.html", {
        "request": request, "domain": DOMAIN, "data": dict(row), "token": token,
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

    # 查看是否有付费订单
    db = get_db()
    try:
        payment = db.execute(
            "SELECT status FROM payments WHERE token=? ORDER BY created_at DESC LIMIT 1",
            (token,)
        ).fetchone()
        total_done = db.execute(
            "SELECT COUNT(*) as cnt FROM tests WHERE status='done'"
        ).fetchone()["cnt"]
    finally:
        db.close()

    payment_status = payment["status"] if payment else None

    return templates.TemplateResponse("me.html", {
        "request": request, "domain": DOMAIN, "data": data, "token": token,
        "payment_status": payment_status, "total_done": total_done,
    })


@app.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard_page(request: Request):
    return templates.TemplateResponse("leaderboard.html", {"request": request, "domain": DOMAIN})
