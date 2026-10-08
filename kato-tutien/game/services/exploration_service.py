from __future__ import annotations

import json
import random
import time

from config import EXPLORE_COOLDOWN, HUNT_COOLDOWN
from game.content.events import EXPLORATION_EVENTS, CHOICE_EVENTS
from game.content.zones import EXPLORE_ZONES
from game.repositories.inventory_repository import InventoryRepository
from game.repositories.player_repository import PlayerRepository
from game.repositories.exploration_repository import ExplorationRepository
from game.rules.cultivation_rules import realm_text
from game.services.combat_service import CombatService
from game.services.quest_service import QuestService
from game.services.world_service import WorldService
from game.services.errors import GameError

STAT_DISPLAY_NAMES = {
    "root": "căn cơ",
    "insight": "ngộ tính",
    "luck": "may mắn",
    "fate": "mệnh số",
    "mind": "đạo tâm",
}

from game.utils import weighted_pick
from game.content.talents import talent_mod, destiny_mod


class ExplorationService:
    def __init__(self, players: PlayerRepository, inventory: InventoryRepository,
                 combat: CombatService, quests: QuestService | None = None, world: WorldService | None = None,
                 rng: random.Random | None = None, pending: ExplorationRepository | None = None):
        self.players = players
        self.inventory = inventory
        if pending is None:
            raise ValueError("ExplorationRepository must be injected by the engine.")
        self.pending_repo = pending
        self.combat = combat
        self.quests = quests
        self.world = world
        self.rng = rng or random.Random()

    def _require(self, user_id: str):
        p = self.players.get(user_id)
        if not p:
            raise GameError("Ngươi chưa bước lên con đường tu hành.")
        return p

    def list_zones(self) -> list[dict]:
        return [{"key": k, "name": z["name"], "min_realm": z["min_realm"],
                 "path": z.get("path", "both"),
                 "enabled": z.get("enabled", True), "description": z.get("description", "")}
                for k, z in EXPLORE_ZONES.items()]

    def set_zone(self, user_id: str, zone_key: str) -> dict:
        p = self._require(user_id)
        z = EXPLORE_ZONES.get(zone_key)
        if not z or not z.get("enabled", True):
            raise GameError("Khu vực không khả dụng.")
        if p.realm_index < z["min_realm"]:
            raise GameError(f"Cần đạt cảnh giới tối thiểu: **{realm_text(z['min_realm'], 1)}**.")
        path = z.get("path", "both")
        if path != "both" and p.path != path:
            label = "Tiên đạo" if path == "tien" else "Ma đạo"
            raise GameError(f"Khu vực này chỉ dành cho **{label}**.")
        p.explore_zone = zone_key
        self.players.save(p)
        return {"zone": z, "key": zone_key, "player": p}

    def pending(self, user_id: str) -> dict | None:
        row = self.pending_repo.get_pending(user_id)
        if not row:
            return None
        payload = json.loads(row["payload"])
        return {"event": payload, "zone_key": row["zone_key"], "created_at": row["created_at"]}

    def _save_pending(self, user_id: str, event: dict, zone_key: str) -> None:
        self.pending_repo.save_pending(user_id, event, zone_key)

    def _clear_pending(self, user_id: str) -> None:
        self.pending_repo.clear_pending(user_id)

    def explore(self, user_id: str, zone_key: str | None = None) -> dict:
        p = self._require(user_id)
        pending = self.pending(user_id)
        if pending:
            return {"choice": True, "event": pending["event"], "zone": EXPLORE_ZONES[pending["zone_key"]], "pending": True}
        now = int(time.time())
        remain = EXPLORE_COOLDOWN - (now - p.last_explore)
        if remain > 0:
            raise GameError(f"Khám phá còn chờ **{remain}s**.")
        key = zone_key or p.explore_zone
        z = EXPLORE_ZONES.get(key)
        if not z or not z.get("enabled", True):
            raise GameError("Khu vực không khả dụng.")
        if p.realm_index < z["min_realm"]:
            raise GameError(f"Cần đạt **{realm_text(z['min_realm'], 1)}** mới có thể tiến vào.")
        path = z.get("path", "both")
        if path != "both" and p.path != path:
            raise GameError("Con đường của ngươi không phù hợp với khu vực này.")
        p.last_explore = now
        if self.world:
            spawned = self.world.maybe_spawn(key)
        else:
            spawned = None
        # 37% chance to enter a multi-choice narrative event.
        choice_chance = min(0.70, 0.37 + float(talent_mod(p.talent, "rare_event", 0.0)) + float(destiny_mod(p.destiny, "luck", 0.0)) * 0.20 + p.fate * 0.001)
        if CHOICE_EVENTS and self.rng.random() < choice_chance:
            candidates = [e for e in CHOICE_EVENTS if not e.get("zones") or key in e["zones"]]
            if candidates:
                event = weighted_pick(self.rng, [(e, e["weight"]) for e in candidates])
                self._save_pending(user_id, event, key)
                self.players.save(p)
                result = {"choice": True, "event": event, "zone": z, "pending": False}
                if spawned:
                    result["world_event"] = spawned
                if self.quests:
                    result["quest_progress"] = self.quests.progress(user_id, "explore_zone", key)
                if getattr(self, "sect_tower", None) is not None:
                    self.sect_tower.record_activity(user_id, "explore", 1)
                return result

        event = weighted_pick(self.rng, [(e, e["weight"]) for e in EXPLORATION_EVENTS])
        result: dict = {"event": event, "zone": z, "text": event.get("text", ""), "combat": False}
        self.players.add_history(user_id, "explore", event["key"])
        if self.quests:
            result_quest = self.quests.progress(user_id, "explore_zone", key)
        else:
            result_quest = []
        if event.get("combat"):
            enc = self.combat.start_encounter(user_id, boss=False)
            result["combat"] = True
            result["encounter"] = enc
            result["quest_progress"] = result_quest
            if spawned:
                result["world_event"] = spawned
            self.players.save(p)
            if getattr(self, "sect_tower", None) is not None:
                self.sect_tower.record_activity(user_id, "explore", 1)
            return result
        self._apply_effect(p, user_id, event, result)
        self.players.save(p)
        result["player"] = p
        result["quest_progress"] = result_quest
        if spawned:
            result["world_event"] = spawned
        if getattr(self, "sect_tower", None) is not None:
            self.sect_tower.record_activity(user_id, "explore", 1)
        return result

    def choose(self, user_id: str, choice_id: str) -> dict:
        p = self._require(user_id)
        pending = self.pending(user_id)
        if not pending:
            raise GameError("Ngươi không có sự kiện nào đang chờ lựa chọn.")
        event = pending["event"]
        choice = next((c for c in event.get("choices", []) if c["id"] == choice_id), None)
        if not choice:
            raise GameError("Lựa chọn không tồn tại hoặc đã hết hiệu lực.")
        condition = choice.get("condition", {})
        for stat, required in condition.items():
            if getattr(p, stat, 0) < required:
                raise GameError(f"Cần {STAT_DISPLAY_NAMES.get(stat, stat)} ≥ {required} để chọn phương án này.")
        result = {"choice": True, "event": event, "selected": choice, "text": choice.get("effect", {}).get("text", "")}
        self._apply_effect(p, user_id, choice.get("effect", {}), result)
        if self.quests:
            result["quest_progress"] = self.quests.progress(user_id, "discovery", next((d for d in [choice.get("effect", {}).get("discover")] if d), "")) if choice.get("effect", {}).get("discover") else []
        self._clear_pending(user_id)
        self.players.add_history(user_id, "choice", f"{event['key']}:{choice_id}")
        self.players.save(p)
        result["player"] = p
        return result

    def _apply_effect(self, p, user_id: str, effect: dict, result: dict) -> None:
        for field, key in (("spirit_stones", "stones"), ("cultivation", "cultivation"), ("injury", "injury")):
            if key not in effect:
                continue
            value = effect[key]
            amount = self.rng.randint(*value) if isinstance(value, list) else int(value)
            if key == "stones":
                amount = int(amount * (1 + p.luck / 200)) if amount > 0 else amount
                p.spirit_stones = max(0, p.spirit_stones + amount)
                result["stones"] = amount
            elif key == "cultivation":
                p.cultivation = max(0, p.cultivation + amount)
                result["cultivation"] = amount
            else:
                p.injury = max(0, min(100, p.injury + amount))
                result["injury"] = amount
        if "insight" in effect:
            p.insight = max(0, min(100, p.insight + int(effect["insight"])))
            result["insight"] = int(effect["insight"])
        if "fate" in effect:
            p.fate = max(0, min(100, p.fate + int(effect["fate"])))
            result["fate"] = int(effect["fate"])
        if "reputation" in effect:
            delta=int(effect["reputation"]); p.reputation += delta; result["reputation"]=delta
        if "dao_insight" in effect and p.dao_type:
            amount=int(effect["dao_insight"]); p.dao_insight += amount
            from game.rules.dao_rules import stage_from_insight
            p.dao_stage=stage_from_insight(p.dao_insight); result["dao_insight"]=amount
        if "item" in effect:
            self.inventory.add(user_id, effect["item"], 1)
            result["item"] = effect["item"]
        if effect.get("discover"):
            result["discovery"] = self.players.add_discovery(user_id, effect["discover"])

    def hunt(self, user_id: str) -> dict:
        p = self._require(user_id)
        now = int(time.time())
        remain = HUNT_COOLDOWN - (now - p.last_hunt)
        if remain > 0:
            raise GameError(f"Săn còn chờ **{remain}s**.")
        p.last_hunt = now
        self.players.save(p)
        from game.content.monsters import BOSS_MONSTERS
        eligible_bosses=[b for b in BOSS_MONSTERS if p.realm_index >= b["min_realm"]]
        boss=bool(eligible_bosses) and self.rng.random() < min(0.15,0.05+p.fate*0.001)
        enc=self.combat.start_encounter(user_id,boss=boss)
        return {"encounter": enc, "player": p, "realm": realm_text(p.realm_index, p.realm_layer)}
