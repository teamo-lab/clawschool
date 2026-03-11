"""龙虾学校 - FastAPI 入口"""
from __future__ import annotations

import time
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .models import AnswerSubmission
from .sampler import sample_questions
from .session import create_session_token, verify_session_token
from .scorer import score_test
from . import storage

BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
PUBLIC_DIR = BASE_DIR / "public"

app = FastAPI(title="龙虾学校", description="OpenClaw 智力测试排行榜")

# 静态文件
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ── SSR 页面 ──────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首页 + 排行榜（服务端渲染，SEO 友好）"""
    entries = storage.get_leaderboard(50)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "entries": entries,
    })


@app.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard_page(request: Request):
    """排行榜独立页面"""
    entries = storage.get_leaderboard(100)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "entries": entries,
    })


# ── Skill 文件 ────────────────────────────────────────

@app.get("/skill.md")
async def skill_file():
    """提供 skill.md 给 OpenClaw agent 读取"""
    skill_path = PUBLIC_DIR / "skill.md"
    return FileResponse(skill_path, media_type="text/markdown; charset=utf-8")


# ── API ───────────────────────────────────────────────

@app.get("/api/test/start")
async def test_start():
    """开始测试：返回 session + 题目（不含答案）"""
    questions = sample_questions(per_dimension=4)  # 每维度4题，共20题
    question_ids = [q.id for q in questions]
    session_id, expires_at = create_session_token(question_ids)

    return {
        "sessionId": session_id,
        "expiresAt": expires_at,
        "questionCount": len(questions),
        "questions": [q.model_dump() for q in questions],
    }


@app.post("/api/test/submit")
async def test_submit(body: AnswerSubmission):
    """提交答案，返回评分报告"""
    session = verify_session_token(body.session_id)
    if not session:
        return {"error": "Invalid or expired session"}, 401

    question_ids = session["question_ids"]
    now_ms = int(time.time() * 1000)

    report = score_test(
        session_id=body.session_id,
        question_ids=question_ids,
        answers=body.answers,
        lobster_name=body.lobster_name or "匿名龙虾",
        model=body.model or "unknown",
        submitted_at=now_ms,
    )

    storage.save_score(report)

    return {
        "iqScore": report.iq_score,
        "tier": report.tier,
        "tierEmoji": report.tier_emoji,
        "totalScore": report.total_score,
        "maxScore": report.max_score,
        "dimensions": [d.model_dump() for d in report.dimensions],
        "results": [r.model_dump() for r in report.results],
        "leaderboardUrl": "https://clawschool.teamolab.com",
    }


@app.get("/api/leaderboard")
async def leaderboard_api(limit: int = 50):
    """排行榜 JSON API"""
    limit = min(limit, 100)
    entries = storage.get_leaderboard(limit)
    return {
        "entries": [e.model_dump() for e in entries],
        "total": len(entries),
    }
