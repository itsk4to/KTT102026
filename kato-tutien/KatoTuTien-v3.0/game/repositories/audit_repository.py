from __future__ import annotations

import time
from game.database.connection import Database


class AuditRepository:
    def __init__(self, db: Database):
        self.db = db

    def log(self, actor_id: str, action: str, target_id: str | None = None, details: str = "") -> None:
        self.db.execute(
            "INSERT INTO admin_audit(actor_id, action, target_id, details, created_at) VALUES(?,?,?,?,?)",
            (actor_id, action, target_id, details, int(time.time())),
        )

    def recent(self, limit: int = 50) -> list[dict]:
        rows = self.db.fetchall(
            "SELECT * FROM admin_audit ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [dict(r) for r in rows]

    def is_admin(self, user_id: str) -> bool:
        row = self.db.fetchone("SELECT 1 FROM admin_users WHERE user_id=?", (user_id,))
        return row is not None

    def add_admin(self, user_id: str) -> None:
        self.db.execute("INSERT OR IGNORE INTO admin_users(user_id) VALUES(?)", (user_id,))

    def remove_admin(self, user_id: str) -> None:
        self.db.execute("DELETE FROM admin_users WHERE user_id=?", (user_id,))
