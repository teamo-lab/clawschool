"""评分逻辑"""
from __future__ import annotations

import re
import unicodedata
from .models import (
    Dimension, DimensionScore, QuestionResult, ScoreReport,
    MatchMode, DIMENSION_LABELS,
)
from .questions import QUESTION_INDEX


def score_test(
    session_id: str,
    question_ids: list[str],
    answers: dict[str, str],
    lobster_name: str,
    model: str,
    submitted_at: int,
) -> ScoreReport:
    results: list[QuestionResult] = []

    for qid in question_ids:
        question = QUESTION_INDEX.get(qid)
        if not question:
            results.append(QuestionResult(
                question_id=qid, dimension=Dimension.LOGIC,
                correct=False, earned=0, max_points=0,
            ))
            continue

        user_answer = (answers.get(qid) or "").strip()
        correct = check_answer(question.answer, user_answer, question.match_mode)

        results.append(QuestionResult(
            question_id=qid,
            dimension=question.dimension,
            correct=correct,
            earned=question.points if correct else 0,
            max_points=question.points,
        ))

    dimensions = compute_dimension_scores(results)
    total_earned = sum(r.earned for r in results)
    total_max = sum(r.max_points for r in results)
    iq_score = round(total_earned / total_max * 300) if total_max > 0 else 0
    tier, tier_emoji = get_tier(iq_score)

    return ScoreReport(
        session_id=session_id,
        total_score=total_earned,
        max_score=total_max,
        iq_score=iq_score,
        tier=tier,
        tier_emoji=tier_emoji,
        dimensions=dimensions,
        results=results,
        lobster_name=lobster_name,
        model=model,
        submitted_at=submitted_at,
    )


def check_answer(expected: str, user_answer: str, mode: MatchMode) -> bool:
    if not user_answer:
        return False

    if mode == MatchMode.EXACT:
        return normalize(user_answer) == normalize(expected)
    elif mode == MatchMode.CONTAINS:
        return normalize(expected) in normalize(user_answer)
    elif mode == MatchMode.REGEX:
        try:
            return bool(re.search(expected, user_answer, re.DOTALL))
        except re.error:
            return False
    return False


def normalize(s: str) -> str:
    """统一小写、去空格和标点"""
    s = s.lower().strip()
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[.,;:!?。，；：！？、]", "", s)
    return s


def compute_dimension_scores(results: list[QuestionResult]) -> list[DimensionScore]:
    scores = []
    for dim in Dimension:
        dim_results = [r for r in results if r.dimension == dim]
        earned = sum(r.earned for r in dim_results)
        max_pts = sum(r.max_points for r in dim_results)
        scores.append(DimensionScore(
            dimension=dim,
            label=DIMENSION_LABELS[dim],
            earned=earned,
            max_points=max_pts,
            percentage=round(earned / max_pts * 100) if max_pts > 0 else 0,
        ))
    return scores


def get_tier(iq: int) -> tuple[str, str]:
    if iq >= 280:
        return "天才龙虾", "🦞👑"
    elif iq >= 240:
        return "超级龙虾", "🦞🌟"
    elif iq >= 200:
        return "聪明龙虾", "🦞✨"
    elif iq >= 150:
        return "普通龙虾", "🦞"
    elif iq >= 100:
        return "迷糊龙虾", "🦞💤"
    elif iq >= 50:
        return "懵懂龙虾", "🦞❓"
    else:
        return "石头龙虾", "🪨"
