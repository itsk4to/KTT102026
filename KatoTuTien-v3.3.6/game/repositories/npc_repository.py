from __future__ import annotations

import json
import time

from game.database.connection import Database


class NPCRepository:
    def __init__(self, db: Database):
        self.db = db

    def get(self, user_id: str, npc_key: str) -> dict:
        row = self.db.fetchone(
            "SELECT * FROM npc_relationships WHERE user_id=? AND npc_key=?",
            (user_id, npc_key),
        )
        if not row:
            return {"user_id": user_id, "npc_key": npc_key, "affinity": 0, "flags": {}, "interactions": 0, "last_interaction": 0}
        data = dict(row)
        try:
            data["flags"] = json.loads(data.get("flags") or "{}")
        except json.JSONDecodeError:
            data["flags"] = {}
        return data

    def save(self, user_id: str, npc_key: str, affinity: int, flags: dict, interactions: int) -> dict:
        now = int(time.time())
        self.db.execute(
            """INSERT INTO npc_relationships(user_id,npc_key,affinity,flags,interactions,last_interaction)
               VALUES(?,?,?,?,?,?)
               ON CONFLICT(user_id,npc_key) DO UPDATE SET affinity=excluded.affinity,
               flags=excluded.flags, interactions=excluded.interactions, last_interaction=excluded.last_interaction""",
            (user_id, npc_key, int(affinity), json.dumps(flags, ensure_ascii=False), int(interactions), now),
        )
        return self.get(user_id, npc_key)
