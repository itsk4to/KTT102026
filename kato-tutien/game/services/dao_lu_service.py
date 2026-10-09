from __future__ import annotations

import time

from game.repositories.dao_lu_repository import DaoLuRepository
from game.services.errors import GameError


class DaoLuService:
    def __init__(self, players, repository: DaoLuRepository | None = None):
        self.players = players
        if repository is None:
            raise ValueError("DaoLuRepository must be injected by the engine.")
        self.repo = repository

    def _require(self, user_id):
        p = self.players.get(user_id)
        if not p:
            raise GameError("Ngươi chưa bước lên con đường tu hành.")
        return p

    @staticmethod
    def _pair(a: str, b: str):
        return (a, b) if a < b else (b, a)

    def partner(self, user_id: str):
        row = self.repo.partner_row(user_id)
        if not row:
            return None
        target = row["user_b"] if row["user_a"] == user_id else row["user_a"]
        return {"user_id": target, "intimacy": int(row["intimacy"])}

    def candidates(self, user_id: str, limit: int = 20):
        self._require(user_id)
        return self.repo.candidates(user_id, limit)

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
        if self.repo.has_request_from(user_id):
            raise GameError("Ngươi đã gửi một lời cầu duyên đang chờ.")
        self.repo.create_request(user_id, target_id)
        return {"target_id": target_id}

    def pending(self, user_id: str):
        self._require(user_id)
        return self.repo.pending_for_target(user_id)

    def cancel_request(self, user_id: str, target_id: str):
        self._require(user_id)
        self.repo.delete_request(user_id, target_id)

    def reject(self, user_id: str, requester_id: str):
        self._require(user_id)
        if not self.repo.request_exists(requester_id, user_id):
            raise GameError("Lời cầu duyên không tồn tại.")
        self.repo.delete_request(requester_id, user_id)
        return {"requester_id": requester_id}

    def accept(self, user_id: str, requester_id: str):
        self._require(user_id)
        if self.partner(user_id):
            raise GameError("Ngươi đã có đạo lữ.")
        if not self.repo.request_exists(requester_id, user_id):
            raise GameError("Lời cầu duyên không tồn tại.")
        a, b = self._pair(user_id, requester_id)
        with self.players.transaction():
            self.repo.delete_requests_from(requester_id)
            self.repo.create_partner(a, b)
        return {"partner_id": requester_id, "intimacy": 0}

    def song_tu(self, user_id: str):
        partner = self.partner(user_id)
        if not partner:
            raise GameError("Ngươi chưa có đạo lữ.")
        now = int(time.time())
        a, b = self._pair(user_id, partner["user_id"])
        if now - self.repo.last_song_tu(a, b) < 3600:
            raise GameError("Song tu cần nghỉ ngơi. Hãy quay lại sau.")
        # Completing song-cultivation grants a modest cultivation bonus to both partners.
        # Apply the bonus atomically so one user's success cannot leave the pair desynchronized.
        p_self = self._require(user_id)
        p_partner = self._require(partner["user_id"])
        from game.rules.cultivation_rules import cultivation_requirement, headroom, realm_text
        bonus_a = self._song_tu_bonus(p_self)
        bonus_b = self._song_tu_bonus(p_partner)
        gain_a = min(headroom(p_self.cultivation, p_self.realm_index, p_self.realm_layer), bonus_a)
        gain_b = min(headroom(p_partner.cultivation, p_partner.realm_index, p_partner.realm_layer), bonus_b)
        with self.players.transaction():
            p_self.cultivation += max(0, gain_a)
            p_partner.cultivation += max(0, gain_b)
            self.players.save(p_self)
            self.players.save(p_partner)
            self.repo.increment_intimacy(a, b, now)
        return {
            "intimacy": partner["intimacy"] + 1,
            "partner_id": partner["user_id"],
            "gain_self": max(0, gain_a),
            "gain_partner": max(0, gain_b),
            "realm_self": realm_text(p_self.realm_index, p_self.realm_layer, p_self.path),
            "realm_partner": realm_text(p_partner.realm_index, p_partner.realm_layer, p_partner.path),
        }

    @staticmethod
    def _song_tu_bonus(player) -> int:
        # Base bonus scales gently with realm while remaining capped.
        return min(500, 100 + max(0, int(player.realm_index)) * 20 + max(0, int(player.realm_layer)) * 5)
