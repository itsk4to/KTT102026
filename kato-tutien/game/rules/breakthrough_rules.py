from __future__ import annotations


def apply_failure_injury(current: int, base_penalty: int, multiplier: float = 1.0) -> int:
    """Return clamped injury after a failed breakthrough."""
    return max(0, min(100, int(current) + max(0, round(int(base_penalty) * float(multiplier)))))
