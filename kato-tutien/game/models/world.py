from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ZoneInfo:
    key: str
    name: str
    min_realm: int
    enabled: bool
    description: str = ""
