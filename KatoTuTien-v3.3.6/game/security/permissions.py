from __future__ import annotations

from config import OWNER_IDS


def is_owner(user_id: str) -> bool:
    return user_id in OWNER_IDS
