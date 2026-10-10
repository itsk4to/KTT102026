from __future__ import annotations

import hmac
import time

from config import ADMIN_PASSWORD, ADMIN_SESSION_TTL


class AdminAuth:
    """Admin auth with one-day sessions persisted in the application database.

    Passwords remain configuration secrets (KATO_ADMIN_PASSWORD), never source
    constants. Session expiry is durable so restarts do not force a new login.
    """

    def __init__(self, db=None, password: str | None = None):
        self.db = db
        # Optional injection makes the password verifier easy to unit-test while
        # normal runtime continues to read the hosting environment secret.
        self._password = ADMIN_PASSWORD if password is None else password
        self._sessions: dict[str, float] = {}
        self._fails: dict[str, list[float]] = {}

    def verify_password(self, password: str) -> bool:
        expected = self._password or ""
        return bool(expected) and hmac.compare_digest(password, expected)

    def grant(self, user_id: str) -> float:
        now = int(time.time())
        expires_at = now + ADMIN_SESSION_TTL
        if self.db is not None:
            self.db.execute(
                "INSERT OR REPLACE INTO admin_sessions(user_id, created_at, expires_at) VALUES(?,?,?)",
                (str(user_id), now, expires_at),
            )
        else:
            self._sessions[str(user_id)] = float(expires_at)
        return float(expires_at)

    def has_session(self, user_id: str) -> bool:
        user_id = str(user_id)
        now = int(time.time())
        if self.db is not None:
            row = self.db.fetchone(
                "SELECT expires_at FROM admin_sessions WHERE user_id=?", (user_id,)
            )
            if row is None:
                return False
            if int(row["expires_at"]) <= now:
                self.db.execute("DELETE FROM admin_sessions WHERE user_id=?", (user_id,))
                return False
            return True

        expires_at = self._sessions.get(user_id, 0)
        if expires_at <= now:
            self._sessions.pop(user_id, None)
            return False
        return True

    def clear(self, user_id: str) -> None:
        user_id = str(user_id)
        self._sessions.pop(user_id, None)
        if self.db is not None:
            self.db.execute("DELETE FROM admin_sessions WHERE user_id=?", (user_id,))

    def too_many_failures(self, user_id: str, window: int = 300, limit: int = 5) -> bool:
        now = time.time()
        fails = [t for t in self._fails.get(str(user_id), []) if now - t < window]
        self._fails[str(user_id)] = fails
        return len(fails) >= limit

    def record_failure(self, user_id: str) -> None:
        self._fails.setdefault(str(user_id), []).append(time.time())
