from __future__ import annotations

import math
import random
import secrets
import time

from game.content.items import ITEMS
from game.services.errors import GameError
from game.repositories.pvp_repository import PvpRepository


class PvpService:
    """Turn-based PvP with atomic wager escrow and restart-safe refunds."""

    def __init__(self, players, inventory, combat, repository: PvpRepository, rng: random.Random | None = None):
        self.players = players
        self.inventory = inventory
        self.combat = combat
        self.repository = repository
        self.rng = rng or random.Random()
        self.challenges: dict[str, dict] = {}
        self.matches: dict[str, dict] = {}
        self.recover_abandoned_matches()

    def _player(self, user_id: str):
        player = self.players.get(str(user_id))
        if not player:
            raise GameError(f"Người chơi `{user_id}` chưa tạo nhân vật.")
        return player

    def _active_user(self, user_id: str) -> bool:
        return any(m.get("status") == "active" and user_id in (m["challenger_id"], m["target_id"]) for m in self.matches.values())

    def _stake(self, kind: str, item_id: str | None, amount: int) -> dict:
        if amount < 1:
            raise GameError("Mức cược phải lớn hơn 0.")
        if kind == "stones":
            return {"type": "stones", "amount": int(amount), "item_id": None}
        if kind != "item":
            raise GameError("Loại cược chỉ có `linhthach` hoặc `vatpham`.")
        item = ITEMS.get(item_id or "")
        if not item or not item.get("price"):
            raise GameError("Vật phẩm cược phải là vật phẩm có giá trong Tiên Phường.")
        return {"type": "item", "amount": int(amount), "item_id": item_id}

    def _opponent_amount(self, stake: dict, challenger_share: int) -> int:
        # Equal stake or challenger contributes 45%/55% of the combined wager.
        if challenger_share == 50:
            return stake["amount"]
        numerator = 100 - challenger_share
        return max(1, math.ceil(stake["amount"] * numerator / challenger_share))

    def challenge(self, challenger_id: str, target_id: str, kind: str, amount: int,
                  item_id: str | None = None, challenger_share: int = 50) -> dict:
        challenger_id, target_id = str(challenger_id), str(target_id)
        if challenger_id == target_id:
            raise GameError("Không thể tự khiêu chiến chính mình.")
        if challenger_share not in (45, 50, 55):
            raise GameError("Tỷ lệ cược chỉ nhận 45, 50 hoặc 55.")
        challenger = self._player(challenger_id)
        self._player(target_id)
        if self._active_user(challenger_id) or self._active_user(target_id):
            raise GameError("Một trong hai người đang ở trong trận PvP khác.")
        stake = self._stake(kind, item_id, amount)
        if kind == "stones":
            if challenger.spirit_stones < amount:
                raise GameError("Ngươi không đủ linh thạch để đặt cược.")
        elif self.inventory.get_count(challenger_id, item_id) < amount:
            raise GameError("Ngươi không đủ vật phẩm để đặt cược.")
        target_amount = self._opponent_amount(stake, challenger_share)
        challenge_id = secrets.token_hex(4)
        data = {
            "id": challenge_id,
            "challenger_id": challenger_id,
            "target_id": target_id,
            "stake": stake,
            "challenger_share": challenger_share,
            "target_amount": target_amount,
            "created_at": int(time.time()),
        }
        self.challenges[challenge_id] = data
        return data

    def get_challenge(self, challenge_id: str) -> dict | None:
        return self.challenges.get(challenge_id)

    def _remove_stake(self, user_id: str, stake: dict) -> None:
        if stake["type"] == "stones":
            p = self._player(user_id)
            if p.spirit_stones < stake["amount"]:
                raise GameError(f"{p.display_name or user_id} không đủ linh thạch cược.")
            p.spirit_stones -= stake["amount"]
            self.players.save(p)
        elif not self.inventory.remove(user_id, stake["item_id"], stake["amount"]):
            item = ITEMS[stake["item_id"]]["name"]
            raise GameError(f"Không đủ **{item}** để cược.")

    def _give_stake(self, user_id: str, stake: dict) -> None:
        if stake["type"] == "stones":
            p = self.players.get(user_id)
            if p:
                p.spirit_stones += int(stake["amount"])
                self.players.save(p)
        else:
            self.inventory.add(user_id, stake["item_id"], int(stake["amount"]))

    def accept(self, challenge_id: str, target_id: str) -> dict:
        challenge = self.challenges.get(challenge_id)
        if not challenge:
            raise GameError("Lời khiêu chiến đã hết hạn hoặc không tồn tại.")
        target_id = str(target_id)
        if target_id != challenge["target_id"]:
            raise GameError("Chỉ người được thách đấu mới được nhận lời.")
        if int(time.time()) - challenge["created_at"] > 180:
            self.challenges.pop(challenge_id, None)
            raise GameError("Lời khiêu chiến đã hết hạn.")
        if self._active_user(challenge["challenger_id"]) or self._active_user(target_id):
            raise GameError("Một trong hai người đang ở trong trận PvP khác.")
        challenger_id = challenge["challenger_id"]
        stake_a = dict(challenge["stake"])
        stake_b = {**stake_a, "amount": challenge["target_amount"]}
        if stake_a["type"] == "stones":
            if self._player(target_id).spirit_stones < stake_b["amount"]:
                raise GameError(f"Ngươi cần {stake_b['amount']:,} linh thạch để nhận lời cược.")
        elif self.inventory.get_count(target_id, stake_b["item_id"]) < stake_b["amount"]:
            item_name = ITEMS[stake_b["item_id"]]["name"]
            raise GameError(f"Ngươi cần {stake_b['amount']} × **{item_name}** để nhận lời cược.")

        p_a = self._player(challenger_id)
        p_b = self._player(target_id)
        stats_a = self.combat.battle_stats(p_a)
        stats_b = self.combat.battle_stats(p_b)
        match = {
            "id": challenge_id,
            "challenger_id": challenger_id,
            "target_id": target_id,
            "challenger_name": p_a.display_name or challenger_id,
            "target_name": p_b.display_name or target_id,
            "stake_a": stake_a,
            "stake_b": stake_b,
            "hp": {challenger_id: int(stats_a["max_hp"]), target_id: int(stats_b["max_hp"])},
            "max_hp": {challenger_id: int(stats_a["max_hp"]), target_id: int(stats_b["max_hp"])},
            "stats": {challenger_id: stats_a, target_id: stats_b},
            "turn": challenger_id,
            "guarded": {challenger_id: False, target_id: False},
            "log": ["Hai bên đã đặt cược. Trận đấu bắt đầu!"],
            "status": "active",
        }
        with self.players.transaction():
            self._remove_stake(challenger_id, stake_a)
            self._remove_stake(target_id, stake_b)
            self.repository.create(challenge_id, self._persistable(match))
        self.challenges.pop(challenge_id, None)
        self.matches[challenge_id] = match
        return match

    @staticmethod
    def _persistable(match: dict) -> dict:
        return {k: v for k, v in match.items() if k not in ("stats",)} | {
            "stats": match["stats"]
        }

    def act(self, match_id: str, user_id: str, action: str = "attack") -> dict:
        match = self.matches.get(match_id)
        user_id = str(user_id)
        if not match or match["status"] != "active":
            raise GameError("Trận PvP không còn hoạt động.")
        if user_id not in (match["challenger_id"], match["target_id"]):
            raise GameError("Ngươi không thuộc trận đấu này.")
        if match["turn"] != user_id:
            raise GameError("Chưa đến lượt của ngươi.")
        if action not in ("attack", "guard"):
            raise GameError("Hành động PvP không hợp lệ.")
        opponent_id = match["target_id"] if user_id == match["challenger_id"] else match["challenger_id"]
        name = match["challenger_name"] if user_id == match["challenger_id"] else match["target_name"]
        opponent_name = match["target_name"] if user_id == match["challenger_id"] else match["challenger_name"]
        if action == "guard":
            match["guarded"][user_id] = True
            match["log"].append(f"🛡️ **{name}** dựng hộ thể, giảm sát thương đòn kế tiếp.")
        else:
            atk = float(match["stats"][user_id]["attack"])
            defense = float(match["stats"][opponent_id]["defense"])
            if self.rng.random() > 0.88:
                match["log"].append(f"💨 **{name}** đánh hụt!")
            else:
                damage = max(1, int(atk * self.rng.uniform(0.85, 1.15) - defense * 0.35))
                if self.rng.random() < float(match["stats"][user_id].get("crit", 0.05)):
                    damage = int(damage * 1.5)
                    match["log"].append("⚡ Bạo kích!")
                if match["guarded"][opponent_id]:
                    damage = max(1, int(damage * 0.55))
                    match["guarded"][opponent_id] = False
                    match["log"].append("🛡️ Hộ thể đã giảm sát thương.")
                match["hp"][opponent_id] = max(0, match["hp"][opponent_id] - damage)
                match["log"].append(f"⚔️ **{name}** gây **{damage}** sát thương lên **{opponent_name}**.")
        match["turn"] = opponent_id
        if match["hp"][opponent_id] <= 0:
            self._settle(match, user_id)
        else:
            self.repository.update(match_id, self._persistable(match))
        return match

    def _settle(self, match: dict, winner_id: str | None) -> None:
        status = "finished" if winner_id else "refunded"
        match["status"] = status
        if winner_id:
            match["winner_id"] = winner_id
            match["loser_id"] = match["target_id"] if winner_id == match["challenger_id"] else match["challenger_id"]
        match["log"].append("🏆 Trận đấu kết thúc! Vật cược đã được trao cho người thắng." if winner_id else "🤝 Trận đấu hòa/hủy; cược đã được hoàn trả.")
        # Payout/refund and status transition must commit atomically to prevent a
        # restart from refunding a wager that was already paid to the winner.
        with self.players.transaction():
            if winner_id is None:
                self._give_stake(match["challenger_id"], match["stake_a"])
                self._give_stake(match["target_id"], match["stake_b"])
            else:
                stake_a, stake_b = match["stake_a"], match["stake_b"]
                if stake_a["type"] == "stones":
                    winner = self._player(winner_id)
                    winner.spirit_stones += stake_a["amount"] + stake_b["amount"]
                    self.players.save(winner)
                else:
                    self.inventory.add(winner_id, stake_a["item_id"], stake_a["amount"] + stake_b["amount"])
            self.repository.update(match["id"], self._persistable(match))
            self.repository.finish(match["id"], status)

    def cancel(self, match_id: str) -> dict | None:
        match = self.matches.get(match_id)
        if not match or match["status"] != "active":
            return match
        self._settle(match, None)
        return match

    def recover_abandoned_matches(self) -> None:
        # No Discord message survives a restart; refund any escrowed active match safely.
        for match in self.repository.active():
            with self.players.transaction():
                self._give_stake(match["challenger_id"], match["stake_a"])
                self._give_stake(match["target_id"], match["stake_b"])
                self.repository.finish(match["match_id"], "refunded")
