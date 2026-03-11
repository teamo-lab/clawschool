"""排行榜存储（文件 JSON）"""
from __future__ import annotations

import json
import os
from pathlib import Path
from .models import ScoreReport, LeaderboardEntry

DATA_DIR = Path(__file__).parent.parent / "data"
SCORES_FILE = DATA_DIR / "scores.json"


def _load_scores() -> list[dict]:
    if not SCORES_FILE.exists():
        return []
    try:
        return json.loads(SCORES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_scores(scores: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SCORES_FILE.write_text(
        json.dumps(scores, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def save_score(report: ScoreReport) -> None:
    scores = _load_scores()
    scores.append({
        "lobster_name": report.lobster_name,
        "model": report.model,
        "iq_score": report.iq_score,
        "tier": report.tier,
        "tier_emoji": report.tier_emoji,
        "submitted_at": report.submitted_at,
    })
    scores.sort(key=lambda x: x["iq_score"], reverse=True)
    _save_scores(scores)


def get_leaderboard(limit: int = 50) -> list[LeaderboardEntry]:
    scores = _load_scores()
    entries = []
    for i, s in enumerate(scores[:limit]):
        entries.append(LeaderboardEntry(
            rank=i + 1,
            lobster_name=s["lobster_name"],
            model=s["model"],
            iq_score=s["iq_score"],
            tier=s["tier"],
            tier_emoji=s["tier_emoji"],
            submitted_at=s["submitted_at"],
        ))
    return entries
