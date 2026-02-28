"""向量检索：cosine_topk、cosine_topk_salience（移植自 memU inmemory/vector）。"""

from __future__ import annotations

import math
from collections.abc import Iterable
from datetime import datetime
from typing import cast

import numpy as np


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-9
    return float(np.dot(a, b) / denom)


def salience_score(
    similarity: float,
    reinforcement_count: int,
    last_reinforced_at: datetime | None,
    recency_decay_days: float = 30.0,
) -> float:
    """结合相似度、强化次数与时间的 salience 分数。"""
    reinforcement_factor = math.log(reinforcement_count + 1)
    if last_reinforced_at is None:
        recency_factor = 0.5
    else:
        tz = last_reinforced_at.tzinfo
        now = datetime.now(tz) if tz else datetime.utcnow()
        days_ago = (now - last_reinforced_at).total_seconds() / 86400
        recency_factor = math.exp(-0.693 * days_ago / recency_decay_days)
    return similarity * reinforcement_factor * recency_factor


def cosine_topk(
    query_vec: list[float],
    corpus: Iterable[tuple[str, list[float] | None]],
    k: int = 5,
) -> list[tuple[str, float]]:
    """Top-k 余弦相似度检索。"""
    ids: list[str] = []
    vecs: list[list[float]] = []
    for _id, vec in corpus:
        if vec is not None:
            ids.append(_id)
            vecs.append(cast(list[float], vec))
    if not vecs:
        return []
    q = np.array(query_vec, dtype=np.float32)
    matrix = np.array(vecs, dtype=np.float32)
    q_norm = np.linalg.norm(q)
    vec_norms = np.linalg.norm(matrix, axis=1)
    scores = matrix @ q / (vec_norms * q_norm + 1e-9)
    n = len(scores)
    actual_k = min(k, n)
    if actual_k == n:
        topk_indices = np.argsort(scores)[::-1]
    else:
        topk_indices = np.argpartition(scores, -actual_k)[-actual_k:]
        topk_indices = topk_indices[np.argsort(scores[topk_indices])[::-1]]
    return [(ids[i], float(scores[i])) for i in topk_indices]


def cosine_topk_salience(
    query_vec: list[float],
    corpus: Iterable[tuple[str, list[float] | None, int, datetime | None]],
    k: int = 5,
    recency_decay_days: float = 30.0,
) -> list[tuple[str, float]]:
    """带 salience 的 top-k 检索。"""
    q = np.array(query_vec, dtype=np.float32)
    scored: list[tuple[str, float]] = []
    for _id, vec, reinforcement_count, last_reinforced_at in corpus:
        if vec is None:
            continue
        v = np.array(cast(list[float], vec), dtype=np.float32)
        sim = _cosine(q, v)
        score = salience_score(similarity=sim, reinforcement_count=reinforcement_count,
                               last_reinforced_at=last_reinforced_at, recency_decay_days=recency_decay_days)
        scored.append((_id, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]


__all__ = ["cosine_topk", "cosine_topk_salience", "salience_score"]
