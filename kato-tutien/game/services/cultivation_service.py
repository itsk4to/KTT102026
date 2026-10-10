from __future__ import annotations

import random
import time

from config import CULTIVATE_COOLDOWN, DAILY_COOLDOWN
from game.content.realms import REALMS, cultivation_requirement, TRIBULATION_REALM_INDEX
from game.content.talents import talent_mod, destiny_mod
from game.repositories.player_repository import PlayerRepository
from game.rules.cultivation_rules import (
    breakthrough_chance,
    cultivate_gain,
    headroom,
    is_max_realm,
    realm_text,
)
from game.services.errors import GameError
from game.rules.breakthrough_rules import (
    apply_failure_injury, breakthrough_recovery_seconds,
    requires_nine_thunder_tribulation, thunder_strike_damage,
)


class CultivationService:
    def __init__(self, players: PlayerRepository, rng: random.Random | None = None, inventory=None):
        self.players = players
        self.rng = rng or random.Random()
        self.inventory = inventory

    def _require(self, user_id: str):
        p = self.players.get(user_id)
        if not p:
            raise GameError("Ngươi chưa bước lên con đường tu hành.")
        return p

    def cultivate(self, user_id: str) -> dict:
        p = self._require(user_id)
        now = int(time.time())
        remain = CULTIVATE_COOLDOWN - (now - p.last_cultivate)
        if remain > 0:
            raise GameError(f"Tu luyện còn chờ **{remain}s**.")
        recovery = max(0, int(p.breakthrough_recovery_until) - now)
        if recovery > 0:
            raise GameError(f"Đang hồi phục sau thất bại đột phá. Còn **{self._format_duration(recovery)}** mới có thể tiếp tục tu luyện.")
        if is_max_realm(p.realm_index, p.realm_layer):
            raise GameError("Đã đạt cảnh giới tối thượng.")
        room = headroom(p.cultivation, p.realm_index, p.realm_layer)
        if room <= 0:
            raise GameError("Tu vi đã đầy. Hãy **đột phá**.")
        gain = min(room, int(cultivate_gain(p.root, p.insight, p.luck) * float(talent_mod(p.talent, "cultivation", 1.0)) * float(destiny_mod(p.destiny, "cultivation", 1.0))))
        p.cultivation += gain
        if p.dao_type:
            p.dao_insight += 1
            from game.rules.dao_rules import stage_from_insight
            p.dao_stage = stage_from_insight(p.dao_insight)
        p.last_cultivate = now
        self.players.save(p)
        if getattr(self, "missions", None) is not None:
            self.missions.track_action(user_id, "cultivate", 1)
        if getattr(self, "sect_tower", None) is not None:
            self.sect_tower.record_activity(user_id, "cultivate", 1)
        return {
            "gain": gain,
            "cultivation": p.cultivation,
            "requirement": cultivation_requirement(p.realm_index, p.realm_layer),
            "realm": realm_text(p.realm_index, p.realm_layer, p.path),
            "player": p,
        }

    def breakthrough_preview(self, user_id: str, foundation_bonus: float = 0.0) -> dict:
        p = self._require(user_id)
        req = cultivation_requirement(p.realm_index, p.realm_layer)
        chance = breakthrough_chance(
            root=p.root, mind=p.mind, insight=p.insight,
            injury=p.injury, dao_stage=p.dao_stage, foundation_bonus=foundation_bonus + float(talent_mod(p.talent, "breakthrough", 0.0)) + float(destiny_mod(p.destiny, "breakthrough", 0.0)) + min(20, max(0, int(p.breakthrough_pity))) / 100.0,
        )
        recovery = max(0, int(p.breakthrough_recovery_until) - int(time.time()))
        needs_thunder = requires_nine_thunder_tribulation(p.realm_index, p.realm_layer)
        _, equipment_resistance = self._thunder_equipment_stats(p)
        combat = getattr(self, "combat", None)
        effective_max_hp = int(combat.battle_stats(p)["max_hp"]) if combat is not None else int(p.max_hp)
        return {
            "ready": p.cultivation >= req and not is_max_realm(p.realm_index, p.realm_layer) and recovery <= 0,
            "chance": chance,
            "pity_points": min(20, max(0, int(p.breakthrough_pity))),
            "pity_bonus": min(20, max(0, int(p.breakthrough_pity))) / 100.0,
            "recovery_remaining": recovery,
            "recovery_until": int(p.breakthrough_recovery_until),
            "requirement": req,
            "cultivation": p.cultivation,
            "realm": realm_text(p.realm_index, p.realm_layer, p.path),
            "needs_tribulation": (
                p.realm_index == TRIBULATION_REALM_INDEX
                and p.realm_layer >= REALMS[TRIBULATION_REALM_INDEX][1]
            ),
            "needs_thunder_tribulation": needs_thunder,
            "thunder_strikes": 9 if needs_thunder else 0,
            "thunder_equipment_resistance": equipment_resistance,
            "current_hp": min(max(0, int(p.hp)), effective_max_hp),
            "max_hp": effective_max_hp,
        }

    @staticmethod
    def _thunder_equipment_stats(player) -> tuple[int, float]:
        """Return equipment defense and resistance from the active loadout."""
        from game.content.items import ITEMS

        defense = max(0, int(player.defense))
        resistance = 0.0
        for item_id in (player.loadout or {}).values():
            if not item_id:
                continue
            item = ITEMS.get(item_id, {})
            defense += max(0, int(item.get("defense", 0)))
            resistance += max(0.0, float(item.get("thunder_resistance", 0.0)))
        return defense, min(0.65, resistance)

    def _resolve_nine_thunder(self, player, target_realm_index: int, consumable_resistance: float = 0.0) -> dict:
        defense, equipment_resistance = self._thunder_equipment_stats(player)
        resistance = min(0.65, equipment_resistance + max(0.0, float(consumable_resistance)))
        defense_reduction = min(0.35, defense / (defense + 280 + target_realm_index * 30))
        total_reduction = min(0.65, resistance + defense_reduction)
        hits = []
        total_damage = 0
        previous_damage = 0
        combat = getattr(self, "combat", None)
        effective_max_hp = (int(combat.battle_stats(player)["max_hp"]) if combat is not None else int(player.max_hp))
        player.hp = min(max(0, int(player.hp)), effective_max_hp)
        for strike in range(1, 10):
            damage = thunder_strike_damage(
                effective_max_hp, target_realm_index, strike, defense=defense,
                resistance=resistance, previous_damage=previous_damage,
            )
            hp_before = max(0, int(player.hp))
            lost = min(hp_before, damage)
            player.hp = max(0, hp_before - damage)
            total_damage += lost
            hits.append({"strike": strike, "damage": lost, "hp_after": int(player.hp)})
            previous_damage = damage
            if player.hp <= 0:
                break
        survived = player.hp > 0 and len(hits) == 9
        return {
            "attempted": True,
            "success": survived,
            "strikes": hits,
            "strikes_survived": len(hits) if survived else max(0, len(hits) - 1),
            "strikes_received": len(hits),
            "total_damage": total_damage,
            "resistance": resistance,
            "defense_reduction": defense_reduction,
            "total_reduction": total_reduction,
            "defense": defense,
            "max_hp": effective_max_hp,
            "target_realm": REALMS[target_realm_index][0] if target_realm_index < len(REALMS) else "Cảnh giới kế tiếp",
        }

    def breakthrough(
        self, user_id: str, foundation_bonus: float = 0.0, *,
        thunder_resistance: float = 0.0, thunder_item_names: list[str] | None = None,
    ) -> dict:
        p = self._require(user_id)
        now = int(time.time())
        recovery = max(0, int(p.breakthrough_recovery_until) - now)
        if recovery > 0:
            raise GameError(f"Đang hồi phục sau thất bại đột phá. Còn **{self._format_duration(recovery)}**.")
        if is_max_realm(p.realm_index, p.realm_layer):
            raise GameError("Đã đạt cảnh giới tối thượng.")
        req = cultivation_requirement(p.realm_index, p.realm_layer)
        if p.cultivation < req:
            raise GameError(f"Chưa đủ tu vi. Cần **{req}**, hiện **{p.cultivation}**.")
        # Final Độ Kiếp still uses the separate Ứng Thiên Kiếp flow.
        _, layers = REALMS[p.realm_index]
        if p.realm_index == TRIBULATION_REALM_INDEX and p.realm_layer >= layers:
            raise GameError("Cần **Ứng Thiên Kiếp** để vượt Độ Kiếp.")
        needs_thunder = requires_nine_thunder_tribulation(p.realm_index, p.realm_layer)
        if needs_thunder and p.hp <= 0:
            raise GameError("Khí huyết đã cạn. Hãy hồi phục HP trước khi mở Cửu Lôi Kiếp.")
        chance = breakthrough_chance(
            root=p.root, mind=p.mind, insight=p.insight,
            injury=p.injury, dao_stage=p.dao_stage, foundation_bonus=foundation_bonus + float(talent_mod(p.talent, "breakthrough", 0.0)) + float(destiny_mod(p.destiny, "breakthrough", 0.0)) + min(20, max(0, int(p.breakthrough_pity))) / 100.0,
        )
        breakthrough_roll_success = self.rng.random() < chance
        success = breakthrough_roll_success
        thunder_result = None
        recovery_seconds = 0
        if breakthrough_roll_success:
            old_hp = int(p.hp)
            if needs_thunder:
                thunder_result = self._resolve_nine_thunder(
                    p, p.realm_index + 1, consumable_resistance=thunder_resistance,
                )
                thunder_result["protection_items"] = list(thunder_item_names or [])
                if not thunder_result["success"]:
                    success = False
                    p.hp = 1  # The failed cultivator is left on the brink, not stuck at 0 HP.
                    p.cultivation = int(p.cultivation * 0.70)
                    p.injury = apply_failure_injury(p.injury, 12, float(talent_mod(p.talent, "injury_mult", 1.0)))
                    p.lifespan = max(1, p.lifespan - 2)
                    recovery_seconds = breakthrough_recovery_seconds(p.realm_index, p.realm_layer, tribulation=True)
                    p.breakthrough_recovery_until = now + recovery_seconds
                    self.players.add_history(user_id, "thunder_tribulation", "fail")
                else:
                    p.breakthrough_recovery_until = 0
                    if p.realm_layer < layers:
                        p.realm_layer += 1
                    else:
                        p.realm_index += 1
                        p.realm_layer = 1
                    p.cultivation = 0
                    p.max_hp += 20 + p.root // 10
                    # Unlike a normal breakthrough, Cửu Lôi Kiếp does not refill HP.
                    p.hp = min(old_hp - thunder_result["total_damage"], p.max_hp)
                    p.attack += 3 + p.insight // 20
                    p.defense += 2 + p.root // 25
                    self.players.add_history(user_id, "breakthrough", realm_text(p.realm_index, p.realm_layer, p.path))
                    self.players.add_history(user_id, "thunder_tribulation", "pass")
            else:
                p.breakthrough_recovery_until = 0
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
                self.players.add_history(user_id, "breakthrough", realm_text(p.realm_index, p.realm_layer, p.path))
        else:
            p.cultivation = int(p.cultivation * 0.85)
            p.injury = apply_failure_injury(p.injury, 5, float(talent_mod(p.talent, "injury_mult", 1.0)))
            recovery_seconds = breakthrough_recovery_seconds(p.realm_index, p.realm_layer)
            p.breakthrough_recovery_until = now + recovery_seconds
        pity_before = min(20, max(0, int(p.breakthrough_pity)))
        if success:
            p.breakthrough_pity = 0
        else:
            p.breakthrough_pity = min(20, pity_before + 5)
        self.players.save(p)
        return {
            "success": success,
            "breakthrough_roll_success": breakthrough_roll_success,
            "pity_before": pity_before,
            "pity_after": p.breakthrough_pity,
            "chance": chance,
            "realm": realm_text(p.realm_index, p.realm_layer, p.path),
            "recovery_seconds": recovery_seconds if not success else 0,
            "thunder_tribulation": thunder_result,
            "player": p,
        }

    def breakthrough_item_bonus(self, user_id: str, item_id: str) -> dict:
        from game.content.items import ITEMS
        item = ITEMS.get(item_id) or {}
        bonus = float(item.get("breakthrough_bonus", 0.0))
        if item.get("type") != "consumable" or bonus <= 0:
            raise GameError("Đạo cụ này không hỗ trợ đột phá.")
        if not self.inventory or self.inventory.get_count(user_id, item_id) < 1:
            raise GameError("Không có đạo cụ này trong túi.")
        return {"bonus": bonus, "item_id": item_id, "item": item}

    @staticmethod
    def _format_duration(seconds: int) -> str:
        seconds = max(0, int(seconds))
        hours, rem = divmod(seconds, 3600)
        minutes, secs = divmod(rem, 60)
        if hours:
            return f"{hours} giờ {minutes} phút" if minutes else f"{hours} giờ"
        if minutes:
            return f"{minutes} phút {secs} giây" if secs else f"{minutes} phút"
        return f"{secs} giây"

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
        reward = 500 + min(p.daily_streak, 30) * 50 + p.realm_index * 100
        p.spirit_stones += reward
        p.last_daily = now
        self.players.save(p)
        return {"stones": reward, "streak": p.daily_streak, "player": p}

    def face_tribulation(self, user_id: str) -> dict:
        p = self._require(user_id)
        now = int(time.time())
        recovery = max(0, int(p.breakthrough_recovery_until) - now)
        if recovery > 0:
            raise GameError(f"Đang hồi phục sau thất bại đột phá. Còn **{self._format_duration(recovery)}**.")
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
            injury=p.injury, dao_stage=p.dao_stage, foundation_bonus=0.1 + min(20, max(0, int(p.breakthrough_pity))) / 100.0,
        )
        success = self.rng.random() < chance
        pity_before = min(20, max(0, int(p.breakthrough_pity)))
        if success:
            p.breakthrough_pity = 0
            p.breakthrough_recovery_until = 0
            p.realm_index += 1
            p.realm_layer = 1
            p.cultivation = 0
            p.max_hp += 50
            p.hp = p.max_hp
            p.attack += 15
            p.defense += 10
            self.players.add_history(user_id, "tribulation", "pass")
        else:
            p.breakthrough_pity = min(20, pity_before + 5)
            p.cultivation = int(p.cultivation * 0.5)
            p.injury = min(100, p.injury + 20)
            p.lifespan = max(1, p.lifespan - 5)
            p.breakthrough_recovery_until = now + breakthrough_recovery_seconds(p.realm_index, p.realm_layer, tribulation=True)
            self.players.add_history(user_id, "tribulation", "fail")
        self.players.save(p)
        return {"success": success, "chance": chance, "pity_before": pity_before, "pity_after": p.breakthrough_pity, "realm": realm_text(p.realm_index, p.realm_layer, p.path), "recovery_seconds": 0 if success else max(0, int(p.breakthrough_recovery_until) - now), "player": p}
