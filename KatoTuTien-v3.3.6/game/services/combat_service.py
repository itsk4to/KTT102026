from __future__ import annotations

import random

from game.content.items import ITEMS
from game.content.monsters import MONSTERS, BOSS_MONSTERS
from game.content.techniques import STATUS_EFFECTS
from game.models.combat import Encounter, StatusEffect
from game.models.player import Player
from game.repositories.inventory_repository import InventoryRepository
from game.repositories.player_repository import PlayerRepository
from game.rules.combat_rules import (
    apply_shield,
    calculate_damage,
    hit_chance,
    mastery_multiplier,
    mastery_stage,
    status_on_hit_chance,
    tick_dot,
)
from game.rules.dao_rules import dao_combat_mods
from game.rules.death_rules import defeat_penalty, apply_injury_cap
from game.services.errors import GameError


class CombatService:
    def __init__(
        self,
        players: PlayerRepository,
        inventory: InventoryRepository,
        rng: random.Random | None = None,
    ):
        self.players = players
        self.inventory = inventory
        self.rng = rng or random.Random()
        self._encounters: dict[str, Encounter] = {}

    def _require(self, user_id: str) -> Player:
        p = self.players.get(user_id)
        if not p:
            raise GameError("Ngươi chưa khai đạo.")
        return p

    def battle_stats(self, player: Player) -> dict:
        mods = dao_combat_mods(player.dao_type, player.dao_stage) if player.dao_type else {}
        atk = player.attack
        defense = player.defense
        hp = player.max_hp
        # equipment from loadout
        for slot, item_id in (player.loadout or {}).items():
            if not item_id:
                continue
            it = ITEMS.get(item_id, {})
            atk += int(it.get("attack", 0))
            defense += int(it.get("defense", 0))
        atk = int(atk * mods.get("atk", 1.0))
        defense = int(defense * mods.get("def", 1.0))
        hp = int(hp * mods.get("hp", 1.0))
        accuracy = 50 + player.insight * 0.3 + mods.get("acc", 1.0) * 10
        evasion = 40 + player.luck * 0.25
        return {
            "attack": atk,
            "defense": defense,
            "max_hp": hp,
            "accuracy": accuracy,
            "evasion": evasion,
        }

    def start_encounter(self, user_id: str, boss: bool = False) -> Encounter:
        p = self._require(user_id)
        pool = BOSS_MONSTERS if boss else MONSTERS
        eligible = [m for m in pool if m["min_realm"] <= p.realm_index]
        if not eligible:
            eligible = pool[:1]
        mon = self.rng.choice(eligible)
        stats = self.battle_stats(p)
        scale = 1.0 + p.realm_index * 0.08
        enc = Encounter(
            player_id=user_id,
            enemy_name=mon["name"],
            enemy_hp=int(mon["hp"] * scale),
            enemy_max_hp=int(mon["hp"] * scale),
            enemy_attack=int(mon["attack"] * scale),
            enemy_defense=int(mon["defense"] * scale),
            player_hp=min(p.hp, stats["max_hp"]),
            player_max_hp=stats["max_hp"],
            is_boss=boss,
        )
        self._encounters[user_id] = enc
        return enc

    def get_encounter(self, user_id: str) -> Encounter | None:
        return self._encounters.get(user_id)

    def _tick_side(self, enc: Encounter, side: str) -> list[str]:
        logs = []
        statuses = enc.player_statuses if side == "player" else enc.enemy_statuses
        max_hp = enc.player_max_hp if side == "player" else enc.enemy_max_hp
        remaining = []
        stunned = False
        slow = 1.0
        shield = 0.0
        for st in statuses:
            meta = STATUS_EFFECTS.get(st.effect_id, {})
            kind = meta.get("kind")
            if kind == "dot":
                dmg = tick_dot(max_hp, meta.get("potency", 0.05) * st.potency)
                if side == "player":
                    enc.player_hp = max(0, enc.player_hp - dmg)
                else:
                    enc.enemy_hp = max(0, enc.enemy_hp - dmg)
                logs.append(f"{'Bạn' if side == 'player' else enc.enemy_name} chịu {dmg} sát thương {meta.get('name', st.effect_id)}.")
            elif kind == "control":
                stunned = True
            elif kind == "slow":
                slow = min(slow, meta.get("potency", 0.7))
            elif kind == "shield":
                shield = max(shield, meta.get("potency", 0.35))
            st.duration -= 1
            if st.duration > 0:
                remaining.append(st)
        if side == "player":
            enc.player_statuses = remaining
        else:
            enc.enemy_statuses = remaining
        return logs, stunned, slow, shield

    def _maybe_apply_status(self, enc: Encounter, side: str, effect_id: str) -> str | None:
        if self.rng.random() > status_on_hit_chance():
            return None
        meta = STATUS_EFFECTS.get(effect_id)
        if not meta:
            return None
        st = StatusEffect(effect_id=effect_id, duration=int(meta["duration"]), potency=1.0)
        if side == "enemy":
            enc.enemy_statuses.append(st)
        else:
            enc.player_statuses.append(st)
        return meta.get("name", effect_id)

    def attack(self, user_id: str) -> dict:
        enc = self._encounters.get(user_id)
        if not enc or enc.finished:
            raise GameError("Không có trận đấu.")
        p = self._require(user_id)
        stats = self.battle_stats(p)
        logs = []
        # player status tick
        plogs, stunned, _, _ = self._tick_side(enc, "player")
        logs.extend(plogs)
        if enc.player_hp <= 0:
            return self._finish(enc, p, False, logs)
        if stunned:
            logs.append("Bạn bị **choáng**, bỏ lượt!")
        else:
            if self.rng.random() < hit_chance(stats["accuracy"], 40):
                dmg = calculate_damage(stats["attack"], enc.enemy_defense, rng=self.rng)
                enc.enemy_hp = max(0, enc.enemy_hp - dmg)
                logs.append(f"Bạn gây **{dmg}** sát thương.")
                applied = self._maybe_apply_status(enc, "enemy", self.rng.choice(["burn", "bleed", "poison"]))
                if applied:
                    logs.append(f"Gây hiệu ứng **{applied}**!")
            else:
                logs.append("Đòn đánh **trượt**!")
        if enc.enemy_hp <= 0:
            return self._finish(enc, p, True, logs)
        return self._enemy_turn(enc, p, stats, logs)

    def skill(self, user_id: str, technique_id: str) -> dict:
        enc = self._encounters.get(user_id)
        if not enc or enc.finished:
            raise GameError("Không có trận đấu.")
        p = self._require(user_id)
        key = f"technique:{technique_id}"
        if not self.players.has_discovery(user_id, key):
            raise GameError("Chưa học công pháp này.")
        item = ITEMS.get(technique_id, {})
        stats = self.battle_stats(p)
        logs = []
        plogs, stunned, _, _ = self._tick_side(enc, "player")
        logs.extend(plogs)
        if enc.player_hp <= 0:
            return self._finish(enc, p, False, logs)
        if stunned:
            logs.append("Bạn bị **choáng**, không thi triển được!")
            return self._enemy_turn(enc, p, stats, logs)
        row = self.players.get_mastery(user_id, technique_id)
        mastery = int(row["mastery"]) if row else 1
        power = float(item.get("skill_power", 1.2)) * mastery_multiplier(mastery)
        dmg = calculate_damage(stats["attack"], enc.enemy_defense, power=power, rng=self.rng)
        enc.enemy_hp = max(0, enc.enemy_hp - dmg)
        logs.append(f"Thi triển **{item.get('name', technique_id)}** gây **{dmg}** sát thương.")
        # gain mastery
        new_m = min(12, mastery + 1)
        self.players.upsert_mastery(user_id, technique_id, new_m, mastery_stage(new_m))
        if enc.enemy_hp <= 0:
            return self._finish(enc, p, True, logs)
        return self._enemy_turn(enc, p, stats, logs)

    def use_item(self, user_id: str, item_id: str) -> dict:
        enc = self._encounters.get(user_id)
        if not enc or enc.finished:
            raise GameError("Không có trận đấu.")
        p = self._require(user_id)
        item = ITEMS.get(item_id)
        if not item or item.get("type") not in ("combat_item", "consumable"):
            raise GameError("Không dùng được trong chiến đấu.")
        if not self.inventory.remove(user_id, item_id, 1):
            raise GameError("Không có vật phẩm.")
        logs = []
        plogs, stunned, _, _ = self._tick_side(enc, "player")
        logs.extend(plogs)
        heal = int(item.get("heal", 0))
        if heal:
            enc.player_hp = min(enc.player_max_hp, enc.player_hp + heal)
            logs.append(f"Hồi **{heal}** HP.")
        stats = self.battle_stats(p)
        if enc.player_hp <= 0:
            return self._finish(enc, p, False, logs)
        return self._enemy_turn(enc, p, stats, logs)

    def flee(self, user_id: str) -> dict:
        enc = self._encounters.get(user_id)
        if not enc:
            raise GameError("Không có trận đấu.")
        if self.rng.random() < 0.65:
            enc.finished = True
            enc.victory = None
            self._encounters.pop(user_id, None)
            return {"fled": True, "logs": ["Rút lui thành công."], "encounter": enc}
        logs = ["Rút lui thất bại!"]
        p = self._require(user_id)
        stats = self.battle_stats(p)
        return self._enemy_turn(enc, p, stats, logs)

    def _enemy_turn(self, enc: Encounter, p: Player, stats: dict, logs: list) -> dict:
        elogs, stunned, _, shield = self._tick_side(enc, "enemy")
        logs.extend(elogs)
        if enc.enemy_hp <= 0:
            return self._finish(enc, p, True, logs)
        if stunned:
            logs.append(f"{enc.enemy_name} bị choáng!")
        else:
            if self.rng.random() < hit_chance(50, stats["evasion"]):
                dmg = calculate_damage(enc.enemy_attack, stats["defense"], rng=self.rng)
                if shield:
                    dmg = apply_shield(dmg, shield)
                enc.player_hp = max(0, enc.player_hp - dmg)
                logs.append(f"{enc.enemy_name} gây **{dmg}** sát thương.")
            else:
                logs.append(f"{enc.enemy_name} đánh **trượt**!")
        if enc.player_hp <= 0:
            return self._finish(enc, p, False, logs)
        enc.log.extend(logs)
        return {"fled": False, "logs": logs, "encounter": enc, "finished": False}

    def _finish(self, enc: Encounter, p: Player, victory: bool, logs: list) -> dict:
        enc.finished = True
        enc.victory = victory
        p.hp = max(1, enc.player_hp) if victory else max(1, int(p.max_hp * 0.3))
        rewards = {}
        if victory:
            stones = self.rng.randint(20, 80) * (2 if enc.is_boss else 1)
            cult = self.rng.randint(10, 40) * (2 if enc.is_boss else 1)
            p.spirit_stones += stones
            p.cultivation += cult
            rewards = {"stones": stones, "cultivation": cult}
            logs.append(f"Chiến thắng! +{stones} linh thạch, +{cult} tu vi.")
        else:
            pen = defeat_penalty(p.realm_index)
            p.injury = apply_injury_cap(p.injury + pen["injury"])
            loss = int(p.cultivation * pen["cultivation_loss_pct"])
            p.cultivation = max(0, p.cultivation - loss)
            logs.append(f"Thất bại. Thương thế +{pen['injury']}.")
        self.players.save(p)
        self._encounters.pop(p.user_id, None)
        enc.log.extend(logs)
        return {"fled": False, "logs": logs, "encounter": enc, "finished": True, "victory": victory, "rewards": rewards, "player": p}

    def learned_skills(self, user_id: str) -> list[dict]:
        result = []
        for iid, it in ITEMS.items():
            if it.get("type") != "technique":
                continue
            if self.players.has_discovery(user_id, f"technique:{iid}"):
                row = self.players.get_mastery(user_id, iid)
                result.append({
                    "id": iid,
                    "name": it["name"],
                    "mastery": int(row["mastery"]) if row else 1,
                    "stage": row["stage"] if row else "Nhập môn",
                })
        return result
