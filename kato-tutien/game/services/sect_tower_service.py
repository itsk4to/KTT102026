from __future__ import annotations
import random
from game.content.sects_content import SECT_TOWER, SECT_MISSIONS
from game.services.errors import GameError


class SectTowerService:
    def __init__(self, players, sects, rng=None):
        self.players = players
        self.sects = sects
        self.rng = rng or random.Random()

    def _member(self, user_id):
        p = self.players.get(user_id)
        if not p or not p.sect_id:
            raise GameError("Ngươi chưa gia nhập tông môn.")
        m = self.sects.get_member(p.sect_id, user_id)
        s = self.sects.get(p.sect_id)
        if not m or not s:
            raise GameError("Dữ liệu tông môn không hợp lệ.")
        return p, m, s

    def overview(self, user_id):
        _, _, s = self._member(user_id)
        return {"floor": s.tower_floor, "max_floor": SECT_TOWER["max_floor"], "sect_level": s.level}

    def challenge(self, user_id):
        p, member, s = self._member(user_id)
        if s.tower_floor >= SECT_TOWER["max_floor"]:
            raise GameError("Tông Tháp đã đạt tầng tối đa.")
        floor = s.tower_floor + 1
        required_level = max(1, (floor + 4) // 5)
        if s.level < required_level:
            raise GameError(f"Tầng {floor} cần Tông Môn cấp {required_level}.")
        chance = min(0.92, 0.55 + s.level * 0.04 + p.realm_index * 0.02)
        success = self.rng.random() < chance
        if success:
            s.tower_floor = floor
            s.exp += 100 + floor * 20
            if s.exp >= s.level * 1000:
                s.exp -= s.level * 1000
                s.level += 1
            self.sects.save(s)
            return {"success": True, "floor": floor, "chance": chance, "sect": s}
        return {"success": False, "floor": s.tower_floor, "chance": chance, "sect": s}

    def upgrade_lingmai(self, user_id):
        _, member, s = self._member(user_id)
        if member.role not in {"Tông Chủ", "Phó Tông Chủ", "Trưởng Lão"}:
            raise GameError("Chỉ quản sự cấp cao mới có thể nâng cấp Linh Mạch.")
        cost = (s.linh_mach_level + 1) * 5000
        if s.treasury < cost:
            raise GameError(f"Kho tông môn cần {cost:,} linh thạch.")
        s.treasury -= cost
        s.linh_mach_level += 1
        self.sects.save(s)
        return {"level": s.linh_mach_level, "cost": cost, "sect": s}

    def claim_mission(self, user_id):
        _, member, s = self._member(user_id)
        import time
        day = time.strftime("%Y-%m-%d")
        if s.mission_day != day:
            keys = list(SECT_MISSIONS)
            s.mission_day = day
            s.mission_key = keys[int(time.time()) % len(keys)]
            s.mission_progress = 0
        mission = SECT_MISSIONS[s.mission_key]
        if s.mission_progress < mission["target"]:
            # One-click contribution mission: members can push the progress.
            s.mission_progress += 1
            self.sects.save(s)
            if s.mission_progress < mission["target"]:
                return {"complete": False, "progress": s.mission_progress, "mission": mission}
        member.contribution += mission["reward_contrib"]
        self.sects.update_member(member)
        s.exp += mission["reward_contrib"] * 2
        s.mission_progress = mission["target"]
        self.sects.save(s)
        return {"complete": True, "progress": s.mission_progress, "mission": mission}
