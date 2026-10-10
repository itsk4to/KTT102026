from __future__ import annotations

import random
import time

from game.content.items import ITEMS, SHOP_CATEGORIES, SHOP_ORDER, item_slot, EQUIP_SLOTS
from game.content.techniques import GACHA_TABLE
from game.content.talents import REDEEM_CODES
from game.repositories.inventory_repository import InventoryRepository
from game.repositories.code_repository import CodeRepository
from game.repositories.market_repository import MarketRepository
from game.repositories.player_repository import PlayerRepository
from game.rules.combat_rules import mastery_stage
from game.rules.cultivation_rules import soft_cap_stat, bounded_cultivation_delta
from game.rules.economy_rules import can_afford, seller_gain, tax_amount
from game.services.errors import GameError
from game.utils import weighted_pick
from config import GACHA_TICKET_ID


class EconomyService:
    def __init__(
        self,
        players: PlayerRepository,
        inventory: InventoryRepository,
        market: MarketRepository,
        rng: random.Random | None = None,
        codes: CodeRepository | None = None,
    ):
        self.players = players
        self._inventory = inventory
        self.market = market
        if codes is None:
            raise ValueError("CodeRepository must be injected by the engine.")
        self.codes = codes
        self.rng = rng or random.Random()

    def _require(self, user_id: str):
        p = self.players.get(user_id)
        if not p:
            raise GameError("Ngươi chưa bước lên con đường tu hành.")
        return p

    # ----- Shop -----
    def shop_catalog(self) -> dict:
        """Return structured shop data — UI only renders this."""
        categories = []
        for cat in SHOP_ORDER:
            items = []
            for iid in SHOP_CATEGORIES.get(cat, []):
                it = ITEMS[iid]
                rarity = it.get("rarity", "Phàm")
                category_emoji = {
                    "Đan dược": "💊", "Bùa chú": "🔮", "Pháp bảo": "💠",
                    "Binh khí": "⚔️", "Công pháp": "📜",
                }.get(cat, "📦")
                rarity_emoji = {"Phàm": "⚪", "Hoàng": "🟢", "Huyền": "🔵", "Địa": "🟣", "Thiên": "🟠", "Tiên": "🔴"}.get(rarity, "⚪")
                effects = []
                for key, label in (("cultivation", "Tu vi"), ("heal", "Hồi HP"), ("max_hp", "HP tối đa"), ("root", "Căn cơ"), ("insight", "Ngộ tính"), ("luck", "May mắn"), ("fate", "Mệnh số"), ("mind", "Đạo tâm"), ("attack", "Công"), ("defense", "Thủ"), ("all_stats", "Toàn bộ thuộc tính")):
                    if it.get(key):
                        effects.append(f"{label} +{it[key]}")
                if it.get("breakthrough_bonus"):
                    effects.append(f"Tỷ lệ đột phá +{it['breakthrough_bonus']:.0%}")
                if it.get("thunder_resistance"):
                    effects.append(f"Kháng lôi +{it['thunder_resistance']:.0%}")
                if it.get("technique_stat") and it.get("technique_bonus"):
                    effects.append(f"Công pháp: +{it['technique_bonus']} {it['technique_stat']}")
                if it.get("skill_power"):
                    effects.append(f"Sức mạnh kỹ năng ×{it['skill_power']:.2f}")
                if not effects:
                    effects.append(it.get("description", "Chưa có mô tả tác dụng."))
                items.append({
                    "id": iid,
                    "name": it["name"],
                    "rarity": rarity,
                    "rarity_emoji": rarity_emoji,
                    "emoji": category_emoji,
                    "price": int(it["price"]),
                    "description": it.get("description", ""),
                    "effects": effects,
                    "type": it.get("type", ""),
                    "category": cat,
                })
            if items:
                categories.append({"name": cat, "items": items})
        return {"categories": categories}

    def buy(self, user_id: str, item_id: str, qty: int = 1) -> dict:
        with self.players.transaction():
            if qty < 1 or qty > 100:
                raise GameError("Số lượng phải từ 1 đến 100.")
            item = ITEMS.get(item_id)
            if not item or "price" not in item:
                raise GameError("Vật phẩm không bán trong tiệm.")
            p = self._require(user_id)
            total = int(item["price"]) * qty
            if not can_afford(p.spirit_stones, total):
                raise GameError(f"Không đủ linh thạch. Cần **{total}**, có **{p.spirit_stones}**.")
            p.spirit_stones -= total
            self._inventory.add(user_id, item_id, qty)
            self.players.save(p)
            if getattr(self, "missions", None) is not None:
                self.missions.track_action(user_id, "purchase", 1)
            return {"item": item, "qty": qty, "total": total, "player": p}

    def _effective_max_hp(self, player) -> int:
        combat = getattr(self, "combat", None)
        if combat is not None:
            return max(1, int(combat.battle_stats(player)["max_hp"]))
        return max(1, int(self.equipment_power(player)["max_hp"]))

    def use_item(self, user_id: str, item_id: str, qty: int = 1) -> dict:
        with self.players.transaction():
            if qty < 1 or qty > 100:
                raise GameError("Số lượng phải từ 1 đến 100.")
            item = ITEMS.get(item_id)
            if not item or item.get("type") not in ("consumable",):
                raise GameError("Không thể dùng vật phẩm này.")
            if item.get("breakthrough_bonus"):
                raise GameError("Đây là đạo cụ đột phá. Hãy mở `.dotpha` và chọn đạo cụ trong giao diện đột phá để dùng đúng công dụng.")
            if item.get("thunder_resistance"):
                raise GameError("Đây là vật phẩm hộ kiếp. Hãy mở `.dotpha` và chọn liều dùng trong giao diện Cửu Lôi Kiếp; đừng dùng trực tiếp trong túi.")
            p = self._require(user_id)
            stat_keys = ("root", "insight", "luck", "fate", "mind", "all_stats")
            has_permanent_stat = any(int(item.get(key, 0)) > 0 for key in stat_keys)
            if has_permanent_stat and qty > 1:
                raise GameError("Vật phẩm tăng chỉ số vĩnh viễn chỉ dùng từng món để tránh lãng phí.")
            stat_marker = f"item_stat_bonus:{item_id}"
            stat_already_claimed = has_permanent_stat and self.players.has_discovery(user_id, stat_marker)
            has_repeatable_effect = bool(item.get("cultivation") or item.get("heal"))
            if stat_already_claimed and not has_repeatable_effect:
                raise GameError("Ngươi đã nhận phần tăng chỉ số vĩnh viễn từ vật phẩm này rồi.")
            if not self._inventory.remove(user_id, item_id, qty):
                raise GameError("Không đủ số lượng.")
            requested_cult = int(item.get("cultivation", 0)) * qty
            cult = bounded_cultivation_delta(p.cultivation, requested_cult, p.realm_index, p.realm_layer)
            heal = int(item.get("heal", 0)) * qty
            notes = []
            if requested_cult:
                p.cultivation += cult
                notes.append(f"+{cult} tu vi" if cult else "Tu vi tầng hiện tại đã đầy; không nhận thêm tu vi")
                if cult < requested_cult:
                    notes.append(f"Đã giới hạn tu vi ở ngưỡng tầng hiện tại ({p.cultivation})")
            if heal:
                # Normalize legacy HP values that may exceed the current loadout cap.
                # The cap includes gear, Dao and talent bonuses via CombatService.
                effective_max_hp = self._effective_max_hp(p)
                p.hp = min(max(0, int(p.hp)), effective_max_hp)
                before_hp = p.hp
                p.hp = min(effective_max_hp, p.hp + heal)
                healed = p.hp - before_hp
                notes.append(f"+{healed} HP" if healed else "Khí huyết đã đầy")
            if has_permanent_stat and not stat_already_claimed:
                for stat in ("root", "insight", "luck", "fate", "mind"):
                    bonus = int(item.get(stat, 0))
                    if bonus:
                        actual = soft_cap_stat(getattr(p, stat), bonus)
                        setattr(p, stat, getattr(p, stat) + actual)
                        if actual:
                            notes.append(f"+{actual} {stat}")
                all_stats = int(item.get("all_stats", 0))
                if all_stats:
                    for stat in ("root", "insight", "luck", "fate", "mind"):
                        actual = soft_cap_stat(getattr(p, stat), all_stats)
                        setattr(p, stat, getattr(p, stat) + actual)
                        if actual:
                            notes.append(f"+{actual} {stat}")
                self.players.add_discovery(user_id, stat_marker)
            elif stat_already_claimed:
                notes.append("Chỉ số vĩnh viễn của vật phẩm này đã nhận trước đó")
            self.players.save(p)
            return {"item": item, "qty": qty, "notes": notes, "player": p,
                    "cultivation_requested": requested_cult, "cultivation_gained": cult}

    def learn_technique(self, user_id: str, item_id: str) -> dict:
        with self.players.transaction():
            item = ITEMS.get(item_id)
            if not item or item.get("type") != "technique":
                raise GameError("Không phải công pháp.")
            p = self._require(user_id)
            if self._inventory.get_count(user_id, item_id) < 1:
                raise GameError("Không có công pháp trong túi.")
            key = f"technique:{item_id}"
            if self.players.has_discovery(user_id, key):
                raise GameError("Đã học công pháp này.")
            if not self._inventory.remove(user_id, item_id, 1):
                raise GameError("Không thể tiêu hao công pháp.")
            self.players.add_discovery(user_id, key)
            stat = item.get("technique_stat")
            bonus = int(item.get("technique_bonus", 0))
            actual = 0
            if stat and bonus:
                actual = soft_cap_stat(getattr(p, stat, 50), bonus)
                setattr(p, stat, getattr(p, stat) + actual)
                self.players.add_discovery(user_id, f"technique_bonus:{item_id}")
            mastery = 1 + min(2, p.insight // 40)
            stage = mastery_stage(mastery)
            self.players.upsert_mastery(user_id, item_id, mastery, stage)
            self.players.save(p)
            return {"item": item, "mastery": mastery, "stage": stage, "stat": stat, "bonus": actual, "player": p}

    def equipment_power(self, player) -> dict:
        """Aggregate visible combat stats including currently equipped gear."""
        attack = int(player.attack)
        defense = int(player.defense)
        max_hp = int(player.max_hp)
        for item_id in (player.loadout or {}).values():
            if not item_id:
                continue
            item = ITEMS.get(item_id, {})
            attack += int(item.get("attack", 0))
            defense += int(item.get("defense", 0))
            max_hp += int(item.get("max_hp", 0))
        return {"attack": attack, "defense": defense, "max_hp": max_hp,
                "power": attack * 2 + defense * 2 + max_hp // 10}

    def equip(self, user_id: str, item_id: str) -> dict:
        with self.players.transaction():
            item = ITEMS.get(item_id)
            if not item or item.get("type") != "equipment":
                raise GameError("Không phải trang bị.")
            p = self._require(user_id)
            if self._inventory.get_count(user_id, item_id) < 1:
                raise GameError("Không có trang bị này trong túi.")
            slot = item_slot(item_id) or item.get("slot") or "artifact"
            if slot not in EQUIP_SLOTS:
                slot = "artifact"
            loadout = dict(p.loadout or {})
            previous_id = loadout.get(slot)
            # Consume the newly equipped item from inventory.
            if not self._inventory.remove(user_id, item_id, 1):
                raise GameError("Không có trang bị này trong túi.")
            # The previous item in this slot returns to the bag.
            if previous_id and previous_id != item_id:
                self._inventory.add(user_id, previous_id, 1)
            # If the same item is already equipped in this slot, don't duplicate or consume it.
            if previous_id == item_id:
                self._inventory.add(user_id, item_id, 1)
                raise GameError("Vật phẩm này đã được trang bị ở ô đó.")
            for other_slot, equipped_id in list(loadout.items()):
                if equipped_id == item_id:
                    loadout[other_slot] = None
            loadout[slot] = item_id
            p.loadout = loadout
            p.equipped = item_id
            p.hp = min(max(0, int(p.hp)), self._effective_max_hp(p))
            self.players.save(p)
            return {"item": item, "slot": slot, "loadout": loadout, "player": p,
                    "replaced_item_id": previous_id, "power": self.equipment_power(p)}

    def unequip(self, user_id: str, slot: str | None = None) -> dict:
        with self.players.transaction():
            p = self._require(user_id)
            loadout = dict(p.loadout or {})
            if slot:
                if slot not in EQUIP_SLOTS:
                    raise GameError("Ô trang bị không hợp lệ. Dùng `.thao` để xem hướng dẫn.")
                item_id = loadout.get(slot)
                if not item_id:
                    raise GameError(f"Ô `{slot}` hiện không có trang bị.")
                self._inventory.add(user_id, item_id, 1)
                loadout[slot] = None
                removed = [item_id]
            else:
                removed = []
                for current_slot, item_id in list(loadout.items()):
                    if item_id:
                        self._inventory.add(user_id, item_id, 1)
                        removed.append(item_id)
                    loadout[current_slot] = None
            p.loadout = loadout
            p.equipped = next((v for v in loadout.values() if v), "")
            p.hp = min(max(0, int(p.hp)), self._effective_max_hp(p))
            self.players.save(p)
            return {"loadout": loadout, "player": p, "removed": removed,
                    "power": self.equipment_power(p)}

    def inventory(self, user_id: str) -> list[dict]:
        stacks = self._inventory.list_items(user_id)
        result = []
        for s in stacks:
            it = ITEMS.get(s.item_id, {"name": s.item_id})
            result.append({"id": s.item_id, "name": it.get("name", s.item_id), "qty": s.quantity, "meta": it})
        return result

    # ----- Market -----
    def market_list(self, user_id: str, item_id: str, qty: int, price: int) -> dict:
        with self.players.transaction():
            if qty < 1 or price < 1:
                raise GameError("Số lượng và giá phải > 0.")
            item = ITEMS.get(item_id)
            if not item or not item.get("marketable"):
                raise GameError("Vật phẩm không thể đăng bán.")
            self._require(user_id)
            if not self._inventory.remove(user_id, item_id, qty):
                raise GameError("Không đủ vật phẩm.")
            total = price * qty
            lid = self.market.create(user_id, item_id, qty, total, price)
            return {"listing_id": lid, "item": item, "qty": qty, "price_each": price, "total": total}

    def market_browse(self, limit: int = 30) -> list[dict]:
        listings = self.market.list_all(limit)
        out = []
        for L in listings:
            it = ITEMS.get(L.item_id, {"name": L.item_id})
            out.append({
                "id": L.id, "item_id": L.item_id, "name": it.get("name"),
                "qty": L.quantity, "price_total": L.price, "price_each": L.unit_price, "seller_id": L.seller_id,
            })
        return out

    def market_buy(self, buyer_id: str, listing_id: int) -> dict:
        with self.players.transaction():
            listing = self.market.get(listing_id)
            if not listing:
                raise GameError("Tin đăng không tồn tại.")
            if listing.seller_id == buyer_id:
                raise GameError("Không thể tự mua tin của mình.")
            buyer = self._require(buyer_id)
            total = listing.price  # price is total for the stack
            if not can_afford(buyer.spirit_stones, total):
                raise GameError(f"Không đủ linh thạch. Cần **{total}**.")
            seller = self.players.get(listing.seller_id)
            if not seller:
                raise GameError("Người bán không còn tồn tại.")
            gain = seller_gain(total)
            tax = tax_amount(total)
            buyer.spirit_stones -= total
            seller.spirit_stones += gain
            self._inventory.add(buyer_id, listing.item_id, listing.quantity)
            self.market.delete(listing_id)
            self.players.save(buyer)
            self.players.save(seller)
            return {
                "item_id": listing.item_id, "qty": listing.quantity,
                "total": total, "seller_gain": gain, "tax": tax, "player": buyer,
            }

    def market_cancel(self, user_id: str, listing_id: int) -> dict:
        with self.players.transaction():
            listing = self.market.get(listing_id)
            if not listing:
                raise GameError("Tin đăng không tồn tại.")
            if listing.seller_id != user_id:
                raise GameError("Không phải tin của ngươi.")
            self._inventory.add(user_id, listing.item_id, listing.quantity)
            self.market.delete(listing_id)
            return {"item_id": listing.item_id, "qty": listing.quantity}

    def transfer(self, from_id: str, to_id: str, amount: int) -> dict:
        with self.players.transaction():
            if amount < 1:
                raise GameError("Số lượng phải > 0.")
            if from_id == to_id:
                raise GameError("Không thể tự chuyển.")
            sender = self._require(from_id)
            receiver = self.players.get(to_id)
            if not receiver:
                raise GameError("Người nhận chưa khai đạo.")
            if not can_afford(sender.spirit_stones, amount):
                raise GameError("Không đủ linh thạch.")
            sender.spirit_stones -= amount
            receiver.spirit_stones += amount
            self.players.save(sender)
            self.players.save(receiver)
            return {"amount": amount, "player": sender}

    def redeem_code(self, user_id: str, code: str) -> dict:
        with self.players.transaction():
            code = code.strip().upper()
            meta = REDEEM_CODES.get(code)
            dynamic = False
            if not meta:
                row = self.codes.get(code)
                if row:
                    if int(row.get("enabled", 1)) == 0:
                        raise GameError("Mật Lệnh này đã bị vô hiệu hóa.")
                    dynamic = True
                    meta = {"stones": int(row["reward_stones"]), "item": row["reward_item"], "qty": int(row["reward_qty"]), "max_uses": int(row["max_uses"]), "used_count": int(row["used_count"])}
            if not meta:
                raise GameError("Mã không hợp lệ.")
            if dynamic and int(meta.get("used_count", 0)) >= int(meta.get("max_uses", 1)):
                raise GameError("Mã đã hết lượt sử dụng.")
            p = self._require(user_id)
            # simple discovery key as redemption flag
            key = f"code:{code}"
            if self.players.has_discovery(user_id, key):
                raise GameError("Đã dùng mã này.")
            self.players.add_discovery(user_id, key)
            stones = int(meta.get("stones", 0))
            p.spirit_stones += stones
            item_id = meta.get("item")
            qty = int(meta.get("qty", 0))
            if item_id and qty:
                self._inventory.add(user_id, item_id, qty)
            self.players.save(p)
            if dynamic:
                self.codes.increment_used(code)
            return {"stones": stones, "item": item_id, "qty": qty, "player": p}

    def gacha(self, user_id: str) -> dict:
        with self.players.transaction():
            p = self._require(user_id)
            if self._inventory.get_count(user_id, GACHA_TICKET_ID) >= 1:
                self._inventory.remove(user_id, GACHA_TICKET_ID, 1)
            elif p.spirit_stones >= 1000:
                p.spirit_stones -= 1000
            else:
                raise GameError("Cần Thiên Cơ Lệnh hoặc 1000 linh thạch.")
            item_id = weighted_pick(self.rng, GACHA_TABLE)
            self._inventory.add(user_id, item_id, 1)
            self.players.save(p)
            return {"item_id": item_id, "item": ITEMS.get(item_id, {}), "player": p}
