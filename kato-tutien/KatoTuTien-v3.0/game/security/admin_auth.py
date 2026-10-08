from __future__ import annotations

import hmac
import time

from config import ADMIN_PASSWORD, ADMIN_SESSION_TTL


class AdminAuth:
    """RAM-only admin sessions."""

    def __init__(self):
        self._sessions: dict[str, float] = {}
        self._fails: dict[str, list[float]] = {}

    def verify_password(self, password: str) -> bool:
        expected = ADMIN_PASSWORD or ""
        return bool(expected) and hmac.compare_digest(password, expected)

    def grant(self, user_id: str) -> float:
        exp = time.time() + ADMIN_SESSION_TTL
        self._sessions[user_id] = exp
        return exp

    def has_session(self, user_id: str) -> bool:
        exp = self._sessions.get(user_id, 0)
        if exp < time.time():
            self._sessions.pop(user_id, None)
            return False
        return True

    def clear(self, user_id: str) -> None:
        self._sessions.pop(user_id, None)

    def too_many_failures(self, user_id: str, window: int = 300, limit: int = 5) -> bool:
        now = time.time()
        fails = [t for t in self._fails.get(user_id, []) if now - t < window]
        self._fails[user_id] = fails
        return len(fails) >= limit

    def record_failure(self, user_id: str) -> None:
        self._fails.setdefault(user_id, []).append(time.time())
