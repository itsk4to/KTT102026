from __future__ import annotations

import time

from game.database.connection import Database


class WorldRepository:
    def __init__(self, db: Database):
        self.db = db

    def active(self) -> list[dict]:
        now = int(time.time())
        rows = self.db.fetchall("SELECT * FROM world_events WHERE status='active' AND expires_at>? ORDER BY created_at DESC", (now,))
        return [dict(r) for r in rows]

    def get(self, event_key: str) -> dict | None:
        row = self.db.fetchone("SELECT * FROM world_events WHERE event_key=? AND status='active'", (event_key,))
        return dict(row) if row else None

    def create(self, event_key: str, zone_key: str, target: int, expires_at: int) -> None:
        self.db.execute(
            "INSERT INTO world_events(event_key, zone_key, progress, target, expires_at, status, created_at) VALUES(?,?,0,?,?, 'active',?)",
            (event_key, zone_key, target, expires_at, int(time.time())),
        )

    def contributed(self, event_key: str, user_id: str) -> bool:
        row = self.db.fetchone("SELECT 1 FROM world_event_contributors WHERE event_key=? AND user_id=?", (event_key, user_id))
        return row is not None

    def contribute(self, event_key: str, user_id: str) -> None:
        self.db.execute("INSERT INTO world_event_contributors(event_key,user_id,created_at) VALUES(?,?,?)", (event_key, user_id, int(time.time())))
        self.db.execute("UPDATE world_events SET progress=progress+1 WHERE event_key=?", (event_key,))

    def finish(self, event_key: str) -> None:
        self.db.execute("UPDATE world_events SET status='completed' WHERE event_key=?", (event_key,))
