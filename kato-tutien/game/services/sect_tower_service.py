from __future__ import annotations

import random
import time

from game.content.sects_content import SECT_MISSIONS, SECT_TOWER
from game.repositories.mission_repository import MissionRepository
from game.services.errors import GameError


class SectTowerService:
    def __init__(self, players, sects, rng=None, missions: MissionRepository | None = None):
        self.players = players
        self.sects = sects
        if missions is None:
            raise ValueError("MissionRepository must be injected by the engine.")
        self.missions = missions
        self.rng = rng or random.Random()

    def _member(self, user_id):
        player = self.players.get(user_id)
        if not player or not player.sect_id:
            raise GameError("Ngươi chưa gia nhập tông môn.")
        member = self.sects.get_member(player.sect_id, user_id)
        sect = self.sects.get(player.sect_id)
        if not member or not sect:
            raise GameError("Dữ liệu tông môn không hợp lệ.")
        return player, member, sect

    def overview(self, user_id):
        _, _, sect = self._member(user_id)
        return {
            "floor": sect.tower_floor,
            "max_floor": SECT_TOWER["max_floor"],
            "sect_level": sect.level,
        }

    def challenge(self, user_id):
        player, _, sect = self._member(user_id)
        if sect.tower_floor >= SECT_TOWER["max_floor"]:
            raise GameError("Tông Tháp đã đạt tầng tối đa.")
        floor = sect.tower_floor + 1
        required_level = max(1, (floor + 4) // 5)
        if sect.level < required_level:
            raise GameError(f"Tầng {floor} cần Tông Môn cấp {required_level}.")
        chance = min(0.92, 0.55 + sect.level * 0.04 + player.realm_index * 0.02)
        success = self.rng.random() < chance
        if success:
            sect.tower_floor = floor
            sect.exp += 100 + floor * 20
            while sect.exp >= sect.level * 1000:
                sect.exp -= sect.level * 1000
                sect.level += 1
            self.sects.save(sect)
        return {
            "success": success,
            "floor": sect.tower_floor,
            "chance": chance,
            "sect": sect,
        }

    def upgrade_lingmai(self, user_id):
        _, member, sect = self._member(user_id)
        if member.role not in {"Tông Chủ", "Phó Tông Chủ", "Trưởng Lão"}:
            raise GameError("Chỉ quản sự cấp cao mới có thể nâng cấp Linh Mạch.")
        cost = (sect.linh_mach_level + 1) * 5000
        if sect.treasury < cost:
            raise GameError(f"Kho tông môn cần {cost:,} linh thạch.")
        with self.players.transaction():
            sect.treasury -= cost
            sect.linh_mach_level += 1
            self.sects.save(sect)
        return {"level": sect.linh_mach_level, "cost": cost, "sect": sect}

    def _daily_key(self, user_id):
        _, _, sect = self._member(user_id)
        day = time.strftime("%Y-%m-%d")
        if sect.mission_day != day or not sect.mission_key:
            keys = list(SECT_MISSIONS)
            sect.mission_day = day
            sect.mission_key = keys[int(time.time()) % len(keys)]
            sect.mission_progress = 0
            self.sects.save(sect)
        return sect, day

    def mission_state(self, user_id):
        sect, day = self._daily_key(user_id)
        row = self.missions.get(user_id, sect.sect_id, sect.mission_key, day)
        mission = SECT_MISSIONS[sect.mission_key]
        return {
            "mission": mission,
            "progress": int(row["progress"]) if row else 0,
            "claimed": bool(row["claimed"]) if row else False,
            "day": day,
        }

    def record_activity(self, user_id: str, mission_key: str, amount: int = 1) -> dict:
        """Record real gameplay activity against the current daily sect mission."""
        player = self.players.get(user_id)
        if not player or not player.sect_id:
            return {"mission": None, "progress": 0, "claimed": False}
        if amount <= 0:
            return self.mission_state(user_id)
        sect, day = self._daily_key(user_id)
        if sect.mission_key != mission_key:
            return self.mission_state(user_id)

        row = self.missions.get(user_id, sect.sect_id, mission_key, day)
        current = int(row["progress"]) if row else 0
        claimed = bool(row["claimed"]) if row else False
        target = int(SECT_MISSIONS[mission_key]["target"])
        progress = min(target, current + int(amount))
        self.missions.upsert(user_id, sect.sect_id, mission_key, progress, day, claimed)
        return {
            "mission": SECT_MISSIONS[mission_key],
            "progress": progress,
            "claimed": claimed,
            "day": day,
        }

    def claim_mission(self, user_id):
        _, member, sect = self._member(user_id)
        state = self.mission_state(user_id)
        mission = state["mission"]
        if state["claimed"]:
            raise GameError("Hôm nay ngươi đã nhận thưởng nhiệm vụ Tông Môn.")
        if state["progress"] < mission["target"]:
            raise GameError(
                f"Chưa hoàn thành: **{state['progress']}/{mission['target']}**."
            )

        with self.players.transaction():
            if not self.missions.claim_once(user_id, sect.sect_id, sect.mission_key, state["day"]):
                raise GameError("Nhiệm vụ đã được nhận thưởng.")
            member.contribution += int(mission["reward_contrib"])
            sect.exp += int(mission["reward_contrib"]) * 2
            self.sects.update_member(member)
            while sect.exp >= sect.level * 1000:
                sect.exp -= sect.level * 1000
                sect.level += 1
            self.sects.save(sect)
        return {
            "complete": True,
            "progress": mission["target"],
            "mission": mission,
            "claimed": True,
        }
