from __future__ import annotations

import time

from game.database.connection import Database


class HeavenlyDaoRepository:
    def __init__(self, db: Database):
        self.db = db

    def list_all(self) -> list[dict]:
        return [dict(r) for r in self.db.fetchall("SELECT * FROM heavenly_rules ORDER BY rule_key")]

    def upsert(self, key: str, text: str, enabled: bool, updated_by: str) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO heavenly_rules(rule_key,rule_text,enabled,updated_by,updated_at) VALUES(?,?,?,?,?)",
            (key, text, 1 if enabled else 0, updated_by, int(time.time())),
        )
