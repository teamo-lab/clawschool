"""数据模型定义"""
from __future__ import annotations

from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class Dimension(str, Enum):
    LOGIC = "logic"
    KNOWLEDGE = "knowledge"
    LANGUAGE = "language"
    MATH = "math"
    INSTRUCTION = "instruction"


DIMENSION_LABELS = {
    Dimension.LOGIC: "逻辑推理",
    Dimension.KNOWLEDGE: "知识广度",
    Dimension.LANGUAGE: "语言理解",
    Dimension.MATH: "数学计算",
    Dimension.INSTRUCTION: "指令遵循",
}


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    INSTRUCTION_FOLLOW = "instruction_follow"


class MatchMode(str, Enum):
    EXACT = "exact"
    CONTAINS = "contains"
    REGEX = "regex"


class Question(BaseModel):
    id: str
    dimension: Dimension
    difficulty: int  # 1-3
    type: QuestionType
    prompt: str
    choices: Optional[list[str]] = None
    answer: str  # 不发给客户端
    match_mode: MatchMode = MatchMode.EXACT
    points: int


class ClientQuestion(BaseModel):
    """发给考生的题目（不含答案）"""
    id: str
    dimension: Dimension
    difficulty: int
    type: QuestionType
    prompt: str
    choices: Optional[list[str]] = None
    points: int


class TestSession(BaseModel):
    session_id: str
    questions: list[ClientQuestion]
    question_count: int
    expires_at: int


class AnswerSubmission(BaseModel):
    """接受 camelCase 或 snake_case"""
    session_id: str = Field(alias="sessionId", default=None)
    answers: dict[str, str]
    lobster_name: str = Field(alias="lobsterName", default="匿名龙虾")
    model: Optional[str] = "unknown"
    gateway_version: Optional[str] = Field(alias="gatewayVersion", default=None)

    class Config:
        populate_by_name = True  # 同时接受 field name 和 alias


class QuestionResult(BaseModel):
    question_id: str
    dimension: Dimension
    correct: bool
    earned: int
    max_points: int


class DimensionScore(BaseModel):
    dimension: Dimension
    label: str
    earned: int
    max_points: int
    percentage: int


class ScoreReport(BaseModel):
    session_id: str
    total_score: int
    max_score: int
    iq_score: int  # 0-300
    tier: str
    tier_emoji: str
    dimensions: list[DimensionScore]
    results: list[QuestionResult]
    lobster_name: str
    model: str
    submitted_at: int
    leaderboard_url: str = "https://clawschool.teamolab.com"


class LeaderboardEntry(BaseModel):
    rank: int
    lobster_name: str
    model: str
    iq_score: int
    tier: str
    tier_emoji: str
    submitted_at: int
