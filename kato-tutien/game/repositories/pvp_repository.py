from __future__ import annotations

import json
import time


class PvpRepository:
    """Persists active wager matches so an interrupted bot can safely refund escrow."""

    def __init__(self, db):
        self.db = db

    def create(self, match_id: str, payload: dict) -> None:
        self.db.execute(
            "INSERT INTO pvp_matches(match_id, payload, status, created_at) VALUES(?,?,?,?)",
            (match_id, json.dumps(payload, ensure_ascii=False), "active", int(time.time())),
        )

    def update(self, match_id: str, payload: dict) -> None:
        self.db.execute(
            "UPDATE pvp_matches SET payload=? WHERE match_id=? AND status='active'",
            (json.dumps(payload, ensure_ascii=False), match_id),
        )

    def finish(self, match_id: str, status: str) -> None:
        self.db.execute("UPDATE pvp_matches SET status=? WHERE match_id=?", (status, match_id))

    def active(self) -> list[dict]:
        rows = self.db.fetchall("SELECT match_id, payload FROM pvp_matches WHERE status='active'")
        return [{"match_id": r["match_id"], **json.loads(r["payload"])} for r in rows]
