"""从题库中按维度分层随机抽题"""
from __future__ import annotations

import random
from .models import Dimension, ClientQuestion
from .questions import QUESTION_BANK


ALL_DIMENSIONS = list(Dimension)


def sample_questions(per_dimension: int = 4) -> list[ClientQuestion]:
    """每个维度随机抽 per_dimension 道题，共 5 * per_dimension 道"""
    selected: list[ClientQuestion] = []

    for dim in ALL_DIMENSIONS:
        pool = [q for q in QUESTION_BANK if q.dimension == dim]
        picked = random.sample(pool, min(per_dimension, len(pool)))
        for q in picked:
            selected.append(ClientQuestion(
                id=q.id,
                dimension=q.dimension,
                difficulty=q.difficulty,
                type=q.type,
                prompt=q.prompt,
                choices=q.choices,
                points=q.points,
            ))

    random.shuffle(selected)
    return selected
