from __future__ import annotations

import json
import time

from game.database.connection import Database


class ExplorationRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_pending(self, user_id: str) -> dict | None:
        row = self.db.fetchone("SELECT * FROM pending_exploration_events WHERE user_id=?", (user_id,))
        return dict(row) if row else None

    def save_pending(self, user_id: str, event: dict, zone_key: str) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO pending_exploration_events(user_id,event_key,zone_key,payload,created_at) VALUES(?,?,?,?,?)",
            (user_id, event["key"], zone_key, json.dumps(event, ensure_ascii=False), int(time.time())),
        )

    def clear_pending(self, user_id: str) -> None:
        self.db.execute("DELETE FROM pending_exploration_events WHERE user_id=?", (user_id,))
