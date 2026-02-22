from __future__ import annotations
import math


def cosine_similarity(a: list[float], b: list[float]) -> float:
    # Defensive: empty vectors should not crash
    if not a or not b or len(a) != len(b):
        return -1.0

    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    denom = math.sqrt(na) * math.sqrt(nb)
    return dot / denom if denom else -1.0