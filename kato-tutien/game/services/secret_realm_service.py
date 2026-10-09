"""Business rules for three-hour, persisted Secret Realm reward cycles."""
from __future__ import annotations

import random
import time

from game.content.secret_realms import SECRET_REALMS, SECRET_REALM_CYCLE_SECONDS
from game.repositories.player_repository import PlayerRepository
from game.repositories.secret_realm_repository import SecretRealmRepository
from game.rules.cultivation_rules import headroom, realm_text
from game.services.errors import GameError


class SecretRealmService:
    def __init__(self, players: PlayerRepository, sessions: SecretRealmRepository,
                 rng: random.Random | None = None, clock=None):
        self.players = players
        self.sessions = sessions
        self.rng = rng or random.Random()
        self.clock = clock or time.time

    def _now(self) -> int:
        return int(self.clock())

    def _require_player(self, user_id: str):
        player = self.players.get(str(user_id))
        if player is None:
            raise GameError("Ngươi chưa khai đạo. Hãy dùng `.tutien` để tạo nhân vật trước.")
        return player

    @staticmethod
    def _remaining(session: dict, now: int) -> int:
        return max(0, int(session["cycle_started_at"]) + SECRET_REALM_CYCLE_SECONDS - now)

    def list_realms(self, user_id: str) -> list[dict]:
        player = self._require_player(user_id)
        active = self.sessions.get(user_id)
        items = []
        for realm in SECRET_REALMS.values():
            item = dict(realm)
            item["unlocked"] = player.realm_index >= int(realm["min_realm"])
            item["selected"] = bool(active and active["realm_key"] == realm["key"])
            item["required_realm"] = realm_text(int(realm["min_realm"]), 1, player.path)
            items.append(item)
        return items

    def status(self, user_id: str) -> dict:
        player = self._require_player(user_id)
        now = self._now()
        session = self.sessions.get(user_id)
        if not session:
            return {"player": player, "session": None, "realm": None, "remaining": None,
                    "ready": False, "now": now, "cycle_seconds": SECRET_REALM_CYCLE_SECONDS,
                    "realms": self.list_realms(user_id)}
        realm = SECRET_REALMS.get(session["realm_key"])
        if realm is None:
            # Recover from a stale content key without blocking the player forever.
            with self.sessions.transaction():
                self.sessions.delete(user_id)
            return self.status(user_id)
        remaining = self._remaining(session, now)
        return {"player": player, "session": session, "realm": realm,
                "remaining": remaining, "ready": remaining <= 0, "now": now,
                "cycle_seconds": SECRET_REALM_CYCLE_SECONDS,
                "realms": self.list_realms(user_id)}

    def select(self, user_id: str, realm_key: str) -> dict:
        player = self._require_player(user_id)
        realm = SECRET_REALMS.get(str(realm_key))
        if realm is None:
            raise GameError("Bí cảnh không tồn tại.")
        if player.realm_index < int(realm["min_realm"]):
            required = realm_text(int(realm["min_realm"]), 1, player.path)
            raise GameError(f"Cần đạt **{required}** mới có thể tiến vào **{realm['name']}**.")

        now = self._now()
        with self.sessions.transaction():
            current = self.sessions.get(user_id)
            if current:
                if current["realm_key"] == realm_key:
                    # Clicking the already-selected realm must never reset the timer.
                    return self.status(user_id)
                current_realm = SECRET_REALMS.get(current["realm_key"], {"name": "Bí cảnh hiện tại"})
                remaining = self._remaining(current, now)
                if remaining <= 0:
                    raise GameError(
                        f"**{current_realm['name']}** đã tích lũy đủ 3 giờ. Hãy nhận thưởng trước khi đổi bí cảnh."
                    )
                raise GameError(
                    f"Ngươi đang tu luyện tại **{current_realm['name']}**. Muốn đổi nơi, hãy rời bí cảnh trước; "
                    f"tiến độ còn lại ({remaining // 60} phút) sẽ bị mất."
                )
            self.sessions.start(user_id, realm_key, now)
        return self.status(user_id)

    def claim(self, user_id: str) -> dict:
        user_id = str(user_id)
        now = self._now()
        with self.sessions.transaction():
            session = self.sessions.get(user_id)
            if not session:
                raise GameError("Ngươi chưa chọn bí cảnh. Dùng `.bicanh` để bắt đầu.")
            realm = SECRET_REALMS.get(session["realm_key"])
            if realm is None:
                self.sessions.delete(user_id)
                raise GameError("Bí cảnh cũ không còn tồn tại. Hãy chọn lại một bí cảnh.")
            remaining = self._remaining(session, now)
            if remaining > 0:
                hours, rem = divmod(remaining, 3600)
                minutes, seconds = divmod(rem, 60)
                raise GameError(f"Chưa đủ 3 giờ. Còn **{hours:02d}:{minutes:02d}:{seconds:02d}** mới nhận được thưởng.")

            player = self._require_player(user_id)
            requested_stones = self.rng.randint(*realm["stones"])
            requested_cultivation = self.rng.randint(*realm["cultivation"])
            stones_gain = max(0, int(requested_stones))
            # One idle payout may fill the current stage, but never bypasses breakthrough stages.
            cultivation_gain = min(max(0, int(requested_cultivation)), headroom(
                player.cultivation, player.realm_index, player.realm_layer
            ))

            # Compare-and-swap prevents duplicate claims if two interactions race.
            if not self.sessions.advance_cycle(user_id, int(session["cycle_started_at"]), now):
                raise GameError("Chu kỳ bí cảnh vừa được xử lý. Hãy làm mới giao diện.")
            player.spirit_stones += stones_gain
            player.cultivation += cultivation_gain
            self.players.save(player)
            self.players.add_history(user_id, "secret_realm_claim", f"{realm['key']}:{stones_gain}:{cultivation_gain}")

        return {
            "realm": realm,
            "stones": stones_gain,
            "cultivation": cultivation_gain,
            "requested_cultivation": requested_cultivation,
            "clamped_cultivation": cultivation_gain < requested_cultivation,
            "claims": int(session.get("claims", 0)) + 1,
            "next_cycle_started_at": now,
            "next_cycle_seconds": SECRET_REALM_CYCLE_SECONDS,
            "player": self.players.get(user_id),
        }

    def leave(self, user_id: str) -> dict:
        user_id = str(user_id)
        now = self._now()
        with self.sessions.transaction():
            session = self.sessions.get(user_id)
            if not session:
                raise GameError("Ngươi hiện không ở trong bí cảnh nào.")
            remaining = self._remaining(session, now)
            if remaining <= 0:
                realm = SECRET_REALMS.get(session["realm_key"], {"name": "Bí cảnh"})
                raise GameError(f"**{realm['name']}** đã đủ thời gian. Hãy nhận thưởng trước khi rời đi.")
            if not self.sessions.delete(user_id):
                raise GameError("Trạng thái bí cảnh vừa thay đổi. Hãy làm mới giao diện.")
        return {"realm": SECRET_REALMS.get(session["realm_key"], {"name": "Bí cảnh"}),
                "remaining_lost": remaining}
