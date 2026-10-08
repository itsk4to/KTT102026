from __future__ import annotations

import random
import time

from config import CULTIVATE_COOLDOWN, DAILY_COOLDOWN
from game.content.realms import REALMS, cultivation_requirement, TRIBULATION_REALM_INDEX
from game.repositories.player_repository import PlayerRepository
from game.rules.cultivation_rules import (
    breakthrough_chance,
    cultivate_gain,
    headroom,
    is_max_realm,
    realm_text,
)
from game.services.errors import GameError


class CultivationService:
    def __init__(self, players: PlayerRepository, rng: random.Random | None = None):
        self.players = players
        self.rng = rng or random.Random()

    def _require(self, user_id: str):
        p = self.players.get(user_id)
        if not p:
            raise GameError("Ngươi chưa khai đạo.")
        return p

    def cultivate(self, user_id: str) -> dict:
        p = self._require(user_id)
        now = int(time.time())
        remain = CULTIVATE_COOLDOWN - (now - p.last_cultivate)
        if remain > 0:
            raise GameError(f"Tu luyện còn chờ **{remain}s**.")
        if is_max_realm(p.realm_index, p.realm_layer):
            raise GameError("Đã đạt cảnh giới tối thượng.")
        room = headroom(p.cultivation, p.realm_index, p.realm_layer)
        if room <= 0:
            raise GameError("Tu vi đã đầy. Hãy **đột phá**.")
        gain = min(room, cultivate_gain(p.root, p.insight, p.luck))
        p.cultivation += gain
        p.last_cultivate = now
        self.players.save(p)
        return {
            "gain": gain,
            "cultivation": p.cultivation,
            "requirement": cultivation_requirement(p.realm_index, p.realm_layer),
            "realm": realm_text(p.realm_index, p.realm_layer),
            "player": p,
        }

    def breakthrough_preview(self, user_id: str) -> dict:
        p = self._require(user_id)
        req = cultivation_requirement(p.realm_index, p.realm_layer)
        chance = breakthrough_chance(
            root=p.root, mind=p.mind, insight=p.insight,
            injury=p.injury, dao_stage=p.dao_stage,
        )
        return {
            "ready": p.cultivation >= req and not is_max_realm(p.realm_index, p.realm_layer),
            "chance": chance,
            "requirement": req,
            "cultivation": p.cultivation,
            "realm": realm_text(p.realm_index, p.realm_layer),
            "needs_tribulation": (
                p.realm_index == TRIBULATION_REALM_INDEX
                and p.realm_layer >= REALMS[TRIBULATION_REALM_INDEX][1]
            ),
        }

    def breakthrough(self, user_id: str) -> dict:
        p = self._require(user_id)
        if is_max_realm(p.realm_index, p.realm_layer):
            raise GameError("Đã đạt cảnh giới tối thượng.")
        req = cultivation_requirement(p.realm_index, p.realm_layer)
        if p.cultivation < req:
            raise GameError(f"Chưa đủ tu vi. Cần **{req}**, hiện **{p.cultivation}**.")
        # Tribulation gate at end of Độ Kiếp
        name, layers = REALMS[p.realm_index]
        if p.realm_index == TRIBULATION_REALM_INDEX and p.realm_layer >= layers:
            raise GameError("Cần **Ứng Thiên Kiếp** để vượt Độ Kiếp.")
        chance = breakthrough_chance(
            root=p.root, mind=p.mind, insight=p.insight,
            injury=p.injury, dao_stage=p.dao_stage,
        )
        success = self.rng.random() < chance
        if success:
            if p.realm_layer < layers:
                p.realm_layer += 1
            else:
                p.realm_index += 1
                p.realm_layer = 1
            p.cultivation = 0
            p.max_hp += 20 + p.root // 10
            p.hp = p.max_hp
            p.attack += 3 + p.insight // 20
            p.defense += 2 + p.root // 25
            self.players.add_history(user_id, "breakthrough", realm_text(p.realm_index, p.realm_layer))
        else:
            p.cultivation = int(p.cultivation * 0.85)
            p.injury = min(100, p.injury + 5)
        self.players.save(p)
        return {
            "success": success,
            "chance": chance,
            "realm": realm_text(p.realm_index, p.realm_layer),
            "player": p,
        }

    def claim_daily(self, user_id: str) -> dict:
        p = self._require(user_id)
        now = int(time.time())
        if now - p.last_daily < DAILY_COOLDOWN:
            remain = DAILY_COOLDOWN - (now - p.last_daily)
            raise GameError(f"Đã nhận thưởng hôm nay. Còn **{remain // 3600} giờ**.")
        # streak
        if now - p.last_daily < DAILY_COOLDOWN * 2:
            p.daily_streak += 1
        else:
            p.daily_streak = 1
        reward = 500 + p.daily_streak * 50 + p.realm_index * 100
        p.spirit_stones += reward
        p.last_daily = now
        self.players.save(p)
        return {"stones": reward, "streak": p.daily_streak, "player": p}

    def face_tribulation(self, user_id: str) -> dict:
        p = self._require(user_id)
        if p.realm_index != TRIBULATION_REALM_INDEX:
            raise GameError("Chỉ Ứng Thiên Kiếp khi ở **Độ Kiếp**.")
        _, layers = REALMS[TRIBULATION_REALM_INDEX]
        if p.realm_layer < layers:
            raise GameError("Cần đạt tầng cao nhất của Độ Kiếp.")
        req = cultivation_requirement(p.realm_index, p.realm_layer)
        if p.cultivation < req:
            raise GameError("Tu vi chưa đủ để ứng kiếp.")
        chance = breakthrough_chance(
            root=p.root, mind=p.mind, insight=p.insight,
            injury=p.injury, dao_stage=p.dao_stage, foundation_bonus=0.1,
        )
        success = self.rng.random() < chance
        if success:
            p.realm_index += 1
            p.realm_layer = 1
            p.cultivation = 0
            p.max_hp += 50
            p.hp = p.max_hp
            p.attack += 15
            p.defense += 10
            self.players.add_history(user_id, "tribulation", "pass")
        else:
            p.cultivation = int(p.cultivation * 0.5)
            p.injury = min(100, p.injury + 20)
            p.lifespan = max(1, p.lifespan - 5)
            self.players.add_history(user_id, "tribulation", "fail")
        self.players.save(p)
        return {"success": success, "chance": chance, "realm": realm_text(p.realm_index, p.realm_layer), "player": p}
