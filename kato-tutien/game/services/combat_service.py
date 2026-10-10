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
from game.rules.cultivation_rules import bounded_cultivation_delta
from game.rules.death_rules import defeat_penalty, apply_injury_cap
from game.content.talents import talent_mod, destiny_mod
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
            raise GameError("Ngươi chưa bước lên con đường tu hành.")
        return p

    def battle_stats(self, player: Player) -> dict:
        mods = dao_combat_mods(player.dao_type, player.dao_stage) if player.dao_type else {}
        atk = player.attack
        defense = player.defense
        hp = player.max_hp
        # Equipped gear contributes to combat stats; equipped items are not inventory stacks.
        for slot, item_id in (player.loadout or {}).items():
            if not item_id:
                continue
            it = ITEMS.get(item_id, {})
            atk += int(it.get("attack", 0))
            defense += int(it.get("defense", 0))
            hp += int(it.get("max_hp", 0))
        atk = int(atk * mods.get("atk", 1.0) * float(talent_mod(player.talent, "combat_atk", 1.0)))
        defense = int(defense * mods.get("def", 1.0))
        hp = int(hp * mods.get("hp", 1.0) * float(talent_mod(player.talent, "combat_hp", 1.0)))
        accuracy = 50 + player.insight * 0.3 + mods.get("acc", 1.0) * 10
        evasion = 40 + player.luck * 0.25
        crit = min(0.50, 0.05 + max(0.0, mods.get("crit", 1.0) - 1.0) + float(talent_mod(player.talent, "combat_crit", 0.0)) + float(destiny_mod(player.destiny, "luck", 0.0)))
        spirit_mult = mods.get("spirit", 1.0) * float(talent_mod(player.talent, "skill_power", 1.0))
        return {"attack": atk, "defense": defense, "max_hp": hp, "accuracy": accuracy, "evasion": evasion, "crit": crit, "spirit_mult": spirit_mult}

    def start_encounter(self, user_id: str, boss: bool = False, zone_key: str | None = None, elite: bool = False) -> Encounter:
        current = self._encounters.get(user_id)
        if current and not current.finished:
            raise GameError("Ngươi vẫn đang trong trận đấu hiện tại. Hãy tiếp tục chiến đấu hoặc bỏ chạy trước khi mở trận mới.")
        p = self._require(user_id)
        pool = BOSS_MONSTERS if boss else MONSTERS
        low, high = max(0, p.realm_index - 1), p.realm_index + 1
        realm_eligible = [m for m in pool if low <= m["min_realm"] <= high]
        eligible = list(realm_eligible)
        if zone_key:
            local = [m for m in realm_eligible if zone_key in m.get("zones", [])]
            general = [m for m in realm_eligible if not m.get("zones")]
            zone_catalog = [m for m in pool if zone_key in m.get("zones", [])]
            if boss:
                # Keep bosses region-appropriate even if a high-level player outgrows
                # the local boss's min_realm window.
                eligible = local or general or zone_catalog or realm_eligible
            elif local and general:
                # Mostly show region-specific creatures, with some familiar roaming beasts.
                eligible = local if self.rng.random() < 0.75 else general
            elif local:
                eligible = local
            elif general:
                eligible = general
            else:
                eligible = zone_catalog or realm_eligible
        if not eligible:
            eligible = [min(pool, key=lambda m: abs(m["min_realm"] - p.realm_index))]
        mon = self.rng.choice(eligible)
        stats = self.battle_stats(p)
        # The existing realm curve stays intact; area scaling is intentionally mild.
        zone_scale = {"hoangnguyen": 1.0, "yeuthusonmach": 1.02, "dongphu": 1.04,
                      "haivuc": 1.06, "mavuc": 1.07, "vancotlang": 1.08, "hukhong": 1.08}.get(zone_key, 1.0)
        scale = (1.0 + p.realm_index * 0.08) * zone_scale * (1.30 if elite else 1.0)
        enemy_name = f"Tinh Anh · {mon['name']}" if elite else mon["name"]
        enc = Encounter(
            player_id=user_id,
            enemy_name=enemy_name,
            enemy_hp=int(mon["hp"] * scale),
            enemy_max_hp=int(mon["hp"] * scale),
            enemy_attack=int(mon["attack"] * scale),
            enemy_defense=int(mon["defense"] * scale),
            player_hp=min(p.hp, stats["max_hp"]),
            player_max_hp=stats["max_hp"],
            is_boss=boss,
            is_elite=elite,
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
        enc.turn_number += 1
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
                crit = self.rng.random() < stats.get("crit", 0.05)
                dmg = calculate_damage(stats["attack"], enc.enemy_defense, rng=self.rng)
                if crit: dmg = int(dmg * 1.75)
                enc.enemy_hp = max(0, enc.enemy_hp - dmg)
                logs.append(f"Bạn {'**BẠO KÍCH** · ' if crit else ''}gây **{dmg}** sát thương.")
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
            raise GameError("Chưa học công pháp này. Hãy dùng `.hoc <ID công pháp>` trước khi chiến đấu.")
        item = ITEMS.get(technique_id)
        if not item or item.get("type") != "technique":
            raise GameError("Công pháp này không còn khả dụng. Hãy mở `.vatpham` để kiểm tra ID.")
        enc.turn_number += 1
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
        power = float(item.get("skill_power", 1.2)) * mastery_multiplier(mastery) * float(stats.get("spirit_mult", 1.0))
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
        enc.turn_number += 1
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
        enc.turn_number += 1
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
        effective_max_hp = max(1, int(self.battle_stats(p)["max_hp"]))
        p.hp = (max(1, min(int(enc.player_hp), effective_max_hp)) if victory
                else max(1, int(effective_max_hp * 0.3)))
        rewards = {}
        if victory and p.dao_type:
            p.dao_insight += 3 if enc.is_boss else 1
            from game.rules.dao_rules import stage_from_insight
            p.dao_stage = stage_from_insight(p.dao_insight)
        if victory:
            reward_mult = 2.0 if enc.is_boss else (1.5 if enc.is_elite else 1.0)
            # Higher stages cost more to sustain; scale combat rewards gently, capped at +65%.
            realm_mult = 1.0 + min(0.65, max(0, int(p.realm_index)) * 0.05)
            stones = int(self.rng.randint(20, 80) * reward_mult * realm_mult)
            requested_cult = int(self.rng.randint(10, 40) * reward_mult * realm_mult * float(talent_mod(p.talent, "cultivation_on_victory", 1.0)))
            cult = bounded_cultivation_delta(p.cultivation, requested_cult, p.realm_index, p.realm_layer)
            p.spirit_stones += stones
            p.cultivation += cult
            rewards = {"stones": stones, "cultivation": cult, "cultivation_requested": requested_cult}
            cult_note = f"+{cult} tu vi" if cult else "không thêm tu vi (đã đầy tầng)"
            logs.append(f"Chiến thắng! +{stones} linh thạch, {cult_note}.")
        else:
            pen = defeat_penalty(p.realm_index)
            p.injury = apply_injury_cap(p.injury + pen["injury"])
            loss = int(p.cultivation * pen["cultivation_loss_pct"])
            p.cultivation = max(0, p.cultivation - loss)
            stones_loss = min(p.spirit_stones, int(p.spirit_stones * pen.get("stones_loss_pct", 0.0)))
            p.spirit_stones = max(0, p.spirit_stones - stones_loss)
            penalty_text = f" Thất thoát {stones_loss} linh thạch." if stones_loss else ""
            logs.append(f"Thất bại. Thương thế +{pen['injury']}.{penalty_text}")
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
