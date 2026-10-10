from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from game.content.recurring_missions import MISSIONS, GROUP_LABELS
from game.repositories.player_mission_repository import PlayerMissionRepository
from game.repositories.player_repository import PlayerRepository
from game.rules.cultivation_rules import bounded_cultivation_delta
from game.services.errors import GameError

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


class PlayerMissionService:
    """Claims are explicit; progress is recorded only after successful actions."""

    def __init__(self, players: PlayerRepository, repository: PlayerMissionRepository):
        self.players = players
        self.repository = repository

    @staticmethod
    def period_key(mission: dict, now: datetime | None = None) -> str:
        group = mission["group"]
        if group == "starter":
            return "ever"
        current = now or datetime.now(VN_TZ)
        if current.tzinfo is None:
            current = current.replace(tzinfo=VN_TZ)
        else:
            current = current.astimezone(VN_TZ)
        if group == "daily":
            return current.strftime("%Y-%m-%d")
        iso = current.isocalendar()
        return f"{iso.year}-W{iso.week:02d}"

    def _require(self, user_id: str):
        player = self.players.get(str(user_id))
        if not player:
            raise GameError("Ngươi chưa bước lên con đường tu hành. Dùng `.tutien` để bắt đầu.")
        return player

    def track_action(self, user_id: str, action: str, amount: int = 1) -> None:
        """Advance matching missions; progress never exceeds the target."""
        if amount <= 0:
            return
        self._require(user_id)
        for mission_id, mission in MISSIONS.items():
            if mission["action"] != action:
                continue
            period = self.period_key(mission)
            self.repository.add_progress(user_id, mission_id, period, amount, int(mission["target"]))

    def list_missions(self, user_id: str, now: datetime | None = None) -> list[dict]:
        self._require(user_id)
        result = []
        for mission_id, definition in MISSIONS.items():
            period = self.period_key(definition, now)
            row = self.repository.get(user_id, mission_id, period) or {
                "progress": 0, "claimed": 0, "period_key": period,
            }
            progress = min(int(definition["target"]), max(0, int(row["progress"])))
            claimed = bool(row["claimed"])
            item = dict(definition)
            item.update({
                "id": mission_id, "period_key": period, "progress": progress,
                "claimed": claimed, "complete": progress >= int(definition["target"]),
                "claimable": progress >= int(definition["target"]) and not claimed,
                "group_label": GROUP_LABELS[definition["group"]],
            })
            result.append(item)
        return result

    def claim(self, user_id: str, mission_id: str) -> dict:
        definition = MISSIONS.get(mission_id)
        if not definition:
            raise GameError("Nhiệm vụ không tồn tại.")
        period = self.period_key(definition)
        with self.players.transaction():
            player = self._require(user_id)
            row = self.repository.get(user_id, mission_id, period)
            target = int(definition["target"])
            if not row or int(row["progress"]) < target:
                current = int(row["progress"]) if row else 0
                raise GameError(f"Nhiệm vụ chưa hoàn thành: **{current}/{target}**.")
            if int(row["claimed"]):
                raise GameError("Phần thưởng nhiệm vụ này đã được nhận rồi.")
            if not self.repository.mark_claimed(user_id, mission_id, period, target):
                raise GameError("Phần thưởng vừa được nhận ở thao tác khác. Hãy làm mới danh sách.")
            stones = max(0, int(definition.get("stones", 0)))
            requested_cultivation = max(0, int(definition.get("cultivation", 0)))
            gained_cultivation = bounded_cultivation_delta(
                player.cultivation, requested_cultivation, player.realm_index, player.realm_layer,
            )
            player.spirit_stones += stones
            player.cultivation += gained_cultivation
            self.players.save(player)
            self.players.add_history(user_id, "mission_claim", f"{mission_id}:{period}")
        return {
            "mission": definition, "stones": stones, "cultivation": gained_cultivation,
            "cultivation_requested": requested_cultivation, "player": player,
        }
