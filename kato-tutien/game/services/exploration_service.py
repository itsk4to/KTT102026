from __future__ import annotations

import random
import time

from config import EXPLORE_COOLDOWN, HUNT_COOLDOWN
from game.content.events import EXPLORATION_EVENTS
from game.content.zones import EXPLORE_ZONES
from game.repositories.inventory_repository import InventoryRepository
from game.repositories.player_repository import PlayerRepository
from game.rules.cultivation_rules import realm_text
from game.services.combat_service import CombatService
from game.services.errors import GameError
from game.utils import weighted_pick


class ExplorationService:
    def __init__(
        self,
        players: PlayerRepository,
        inventory: InventoryRepository,
        combat: CombatService,
        rng: random.Random | None = None,
    ):
        self.players = players
        self.inventory = inventory
        self.combat = combat
        self.rng = rng or random.Random()

    def _require(self, user_id: str):
        p = self.players.get(user_id)
        if not p:
            raise GameError("Ngươi chưa khai đạo.")
        return p

    def list_zones(self) -> list[dict]:
        out = []
        for key, z in EXPLORE_ZONES.items():
            out.append({
                "key": key,
                "name": z["name"],
                "min_realm": z["min_realm"],
                "enabled": z.get("enabled", True),
                "description": z.get("description", ""),
            })
        return out

    def set_zone(self, user_id: str, zone_key: str) -> dict:
        p = self._require(user_id)
        z = EXPLORE_ZONES.get(zone_key)
        if not z or not z.get("enabled", True):
            raise GameError("Khu vực không khả dụng.")
        if p.realm_index < z["min_realm"]:
            raise GameError(f"Cần cảnh giới tối thiểu index {z['min_realm']}.")
        p.explore_zone = zone_key
        self.players.save(p)
        return {"zone": z, "key": zone_key, "player": p}

    def explore(self, user_id: str, zone_key: str | None = None) -> dict:
        p = self._require(user_id)
        now = int(time.time())
        remain = EXPLORE_COOLDOWN - (now - p.last_explore)
        if remain > 0:
            raise GameError(f"Khám phá còn chờ **{remain}s**.")
        key = zone_key or p.explore_zone
        z = EXPLORE_ZONES.get(key)
        if not z or not z.get("enabled", True):
            raise GameError("Khu vực không khả dụng.")
        if p.realm_index < z["min_realm"]:
            raise GameError("Cảnh giới chưa đủ.")
        p.last_explore = now
        # weighted event
        entries = [(e, e["weight"]) for e in EXPLORATION_EVENTS]
        event = weighted_pick(self.rng, entries)
        result: dict = {"event": event, "zone": z, "text": event.get("text", ""), "combat": False}
        if event.get("combat"):
            enc = self.combat.start_encounter(user_id, boss=False)
            result["combat"] = True
            result["encounter"] = enc
            self.players.save(p)
            return result
        if "stones" in event:
            lo, hi = event["stones"]
            gain = self.rng.randint(lo, hi)
            # luck bonus
            gain = int(gain * (1 + p.luck / 200))
            p.spirit_stones += gain
            result["stones"] = gain
        if "cultivation" in event:
            lo, hi = event["cultivation"]
            gain = self.rng.randint(lo, hi)
            p.cultivation += gain
            result["cultivation"] = gain
        if "injury" in event:
            lo, hi = event["injury"]
            inj = self.rng.randint(lo, hi)
            p.injury = min(100, p.injury + inj)
            result["injury"] = inj
        if "insight" in event:
            p.insight = min(100, p.insight + int(event["insight"]))
        if "item" in event:
            self.inventory.add(user_id, event["item"], 1)
            result["item"] = event["item"]
        self.players.save(p)
        result["player"] = p
        return result

    def hunt(self, user_id: str) -> dict:
        p = self._require(user_id)
        now = int(time.time())
        remain = HUNT_COOLDOWN - (now - p.last_hunt)
        if remain > 0:
            raise GameError(f"Săn còn chờ **{remain}s**.")
        p.last_hunt = now
        self.players.save(p)
        enc = self.combat.start_encounter(user_id, boss=self.rng.random() < 0.15)
        return {"encounter": enc, "player": p, "realm": realm_text(p.realm_index, p.realm_layer)}
