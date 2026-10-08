from __future__ import annotations
import time
from game.services.errors import GameError


class DaoLuService:
    def __init__(self, players):
        self.players = players
        self.db = players.db

    def _require(self, user_id):
        p = self.players.get(user_id)
        if not p:
            raise GameError("Ngươi chưa bước lên con đường tu hành.")
        return p

    @staticmethod
    def _pair(a: str, b: str):
        return (a, b) if a < b else (b, a)

    def partner(self, user_id: str):
        row = self.db.fetchone("SELECT * FROM dao_lu WHERE user_a=? OR user_b=?", (user_id, user_id))
        if not row:
            return None
        target = row["user_b"] if row["user_a"] == user_id else row["user_a"]
        return {"user_id": target, "intimacy": int(row["intimacy"])}

    def candidates(self, user_id: str, limit: int = 20):
        self._require(user_id)
        rows = self.db.fetchall(
            "SELECT user_id, display_name, path, realm_index, realm_layer FROM players WHERE user_id<>? ORDER BY realm_index DESC, realm_layer DESC LIMIT ?",
            (user_id, limit),
        )
        return [dict(r) for r in rows]

    def request(self, user_id: str, target_id: str):
        self._require(user_id)
        if user_id == target_id:
            raise GameError("Đạo lữ không thể là chính mình.")
        if self.partner(user_id):
            raise GameError("Ngươi đã có đạo lữ.")
        if not self.players.get(target_id):
            raise GameError("Không tìm thấy đạo hữu.")
        if self.partner(target_id):
            raise GameError("Đạo hữu này đã có đạo lữ.")
        row = self.db.fetchone("SELECT 1 FROM dao_lu_requests WHERE requester_id=?", (user_id,))
        if row:
            raise GameError("Ngươi đã gửi một lời cầu duyên đang chờ.")
        self.db.execute("INSERT OR REPLACE INTO dao_lu_requests(requester_id,target_id,created_at) VALUES(?,?,?)", (user_id, target_id, int(time.time())))
        return {"target_id": target_id}

    def pending(self, user_id: str):
        self._require(user_id)
        rows = self.db.fetchall(
            "SELECT r.requester_id, p.display_name FROM dao_lu_requests r JOIN players p ON p.user_id=r.requester_id WHERE r.target_id=?",
            (user_id,),
        )
        return [dict(r) for r in rows]

    def accept(self, user_id: str, requester_id: str):
        self._require(user_id)
        if self.partner(user_id):
            raise GameError("Ngươi đã có đạo lữ.")
        row = self.db.fetchone("SELECT 1 FROM dao_lu_requests WHERE requester_id=? AND target_id=?", (requester_id, user_id))
        if not row:
            raise GameError("Lời cầu duyên không tồn tại.")
        a, b = self._pair(user_id, requester_id)
        with self.db.transaction():
            self.db.execute("DELETE FROM dao_lu_requests WHERE requester_id=?", (requester_id,))
            self.db.execute("INSERT OR REPLACE INTO dao_lu(user_a,user_b,intimacy,last_song_tu) VALUES(?,?,0,0)", (a, b))
        return {"partner_id": requester_id, "intimacy": 0}

    def song_tu(self, user_id: str):
        p = self.partner(user_id)
        if not p:
            raise GameError("Ngươi chưa có đạo lữ.")
        now = int(time.time())
        a, b = self._pair(user_id, p["user_id"])
        row = self.db.fetchone("SELECT last_song_tu FROM dao_lu WHERE user_a=? AND user_b=?", (a, b))
        if row and now - int(row["last_song_tu"]) < 3600:
            raise GameError("Song tu cần nghỉ ngơi. Hãy quay lại sau.")
        self.db.execute("UPDATE dao_lu SET intimacy=intimacy+1,last_song_tu=? WHERE user_a=? AND user_b=?", (now, a, b))
        return {"intimacy": p["intimacy"] + 1, "partner_id": p["user_id"]}
