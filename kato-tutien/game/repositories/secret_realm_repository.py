"""Persistence boundary for one active Secret Realm session per player."""
from __future__ import annotations

from game.database.connection import Database


class SecretRealmRepository:
    def __init__(self, db: Database):
        self.db = db

    def transaction(self):
        return self.db.transaction()

    def get(self, user_id: str) -> dict | None:
        row = self.db.fetchone(
            "SELECT user_id, realm_key, cycle_started_at, claims FROM secret_realm_sessions WHERE user_id=?",
            (str(user_id),),
        )
        return dict(row) if row else None

    def start(self, user_id: str, realm_key: str, started_at: int) -> None:
        self.db.execute(
            "INSERT INTO secret_realm_sessions(user_id, realm_key, cycle_started_at, claims) VALUES(?,?,?,0)",
            (str(user_id), realm_key, int(started_at)),
        )

    def advance_cycle(self, user_id: str, expected_started_at: int, next_started_at: int) -> bool:
        cur = self.db.execute(
            "UPDATE secret_realm_sessions SET cycle_started_at=?, claims=claims+1 "
            "WHERE user_id=? AND cycle_started_at=?",
            (int(next_started_at), str(user_id), int(expected_started_at)),
        )
        return cur.rowcount == 1

    def delete(self, user_id: str) -> bool:
        cur = self.db.execute("DELETE FROM secret_realm_sessions WHERE user_id=?", (str(user_id),))
        return cur.rowcount == 1
