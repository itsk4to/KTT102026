from __future__ import annotations

import random


def weighted_pick(rng: random.Random, entries):
    population = [item for item, _w in entries]
    weights = [w for _i, w in entries]
    return rng.choices(population, weights=weights, k=1)[0]


def fmt_amount(value: int) -> str:
    return f"{int(value):,}".replace(",", ".")
