from __future__ import annotations

import time

from game.database.connection import Database


class DaoLuRepository:
    def __init__(self, db: Database):
        self.db = db

    def partner_row(self, user_id: str):
        return self.db.fetchone("SELECT * FROM dao_lu WHERE user_a=? OR user_b=?", (user_id, user_id))

    def candidates(self, user_id: str, limit: int = 20) -> list[dict]:
        rows = self.db.fetchall(
            "SELECT user_id, display_name, path, realm_index, realm_layer "
            "FROM players WHERE user_id<>? ORDER BY realm_index DESC, realm_layer DESC LIMIT ?",
            (user_id, limit),
        )
        return [dict(r) for r in rows]

    def has_request_from(self, requester_id: str) -> bool:
        return self.db.fetchone("SELECT 1 FROM dao_lu_requests WHERE requester_id=?", (requester_id,)) is not None

    def create_request(self, requester_id: str, target_id: str) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO dao_lu_requests(requester_id,target_id,created_at) VALUES(?,?,?)",
            (requester_id, target_id, int(time.time())),
        )

    def pending_for_target(self, target_id: str) -> list[dict]:
        rows = self.db.fetchall(
            "SELECT r.requester_id, p.display_name "
            "FROM dao_lu_requests r JOIN players p ON p.user_id=r.requester_id WHERE r.target_id=?",
            (target_id,),
        )
        return [dict(r) for r in rows]

    def request_exists(self, requester_id: str, target_id: str) -> bool:
        return self.db.fetchone(
            "SELECT 1 FROM dao_lu_requests WHERE requester_id=? AND target_id=?",
            (requester_id, target_id),
        ) is not None

    def delete_request(self, requester_id: str, target_id: str) -> None:
        self.db.execute(
            "DELETE FROM dao_lu_requests WHERE requester_id=? AND target_id=?",
            (requester_id, target_id),
        )

    def delete_requests_from(self, requester_id: str) -> None:
        self.db.execute("DELETE FROM dao_lu_requests WHERE requester_id=?", (requester_id,))

    def create_partner(self, user_a: str, user_b: str) -> None:
        self.db.execute(
            "INSERT OR REPLACE INTO dao_lu(user_a,user_b,intimacy,last_song_tu) VALUES(?,?,0,0)",
            (user_a, user_b),
        )

    def last_song_tu(self, user_a: str, user_b: str) -> int:
        row = self.db.fetchone(
            "SELECT last_song_tu FROM dao_lu WHERE user_a=? AND user_b=?",
            (user_a, user_b),
        )
        return int(row["last_song_tu"]) if row else 0

    def increment_intimacy(self, user_a: str, user_b: str, now: int) -> None:
        self.db.execute(
            "UPDATE dao_lu SET intimacy=intimacy+1,last_song_tu=? WHERE user_a=? AND user_b=?",
            (now, user_a, user_b),
        )
