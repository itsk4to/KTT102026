from __future__ import annotations

from game.content.npcs import NPCS
from game.content.quests import QUESTS
from game.content.items import ITEMS
from game.repositories.player_repository import PlayerRepository
from game.repositories.quest_repository import QuestRepository
from game.services.errors import GameError

STAT_DISPLAY_NAMES = {
    "root": "căn cơ",
    "insight": "ngộ tính",
    "luck": "may mắn",
    "fate": "mệnh số",
    "mind": "đạo tâm",
}



class QuestService:
    def __init__(self, players: PlayerRepository, quests: QuestRepository, inventory, npc_service=None):
        self.players = players
        self.quests = quests
        self.inventory = inventory
        self.npc_service = npc_service

    def _require(self, user_id: str):
        p = self.players.get(user_id)
        if not p:
            raise GameError("Ngươi chưa bước lên con đường tu hành.")
        return p

    def list_available(self, user_id: str) -> list[dict]:
        self._require(user_id)
        active = {q["quest_key"] for q in self.quests.active(user_id)}
        result = []
        for key, quest in QUESTS.items():
            if key in active or self.quests.has_completed(user_id, key):
                continue
            npc = NPCS.get(quest["npc"], {})
            result.append({"key": key, "name": quest["name"], "description": quest["description"], "npc": npc.get("name", quest["npc"])})
        return result

    def start(self, user_id: str, quest_key: str) -> dict:
        self._require(user_id)
        quest = QUESTS.get(quest_key)
        if not quest:
            raise GameError("Nhiệm vụ không tồn tại.")
        if self.quests.get(user_id, quest_key):
            raise GameError("Ngươi đã từng nhận nhiệm vụ này.")
        self.quests.start(user_id, quest_key)
        if self.npc_service:
            self.npc_service.remember(user_id, quest["npc"], 1, "accepted_" + quest_key)
        return self.status(user_id, quest_key)

    def active(self, user_id: str) -> list[dict]:
        self._require(user_id)
        return [self.status(user_id, row["quest_key"]) for row in self.quests.active(user_id)]

    def status(self, user_id: str, quest_key: str) -> dict:
        row = self.quests.get(user_id, quest_key)
        quest = QUESTS.get(quest_key)
        if not row or not quest:
            raise GameError("Nhiệm vụ không tồn tại.")
        step = min(int(row["step"]), len(quest["steps"]) - 1)
        current = quest["steps"][step]
        return {"key": quest_key, "quest": quest, "row": row, "step": current, "done": row["status"] == "completed"}

    def progress(self, user_id: str, kind: str, target: str, amount: int = 1) -> list[str]:
        messages: list[str] = []
        for row in self.quests.active(user_id):
            quest = QUESTS.get(row["quest_key"])
            if not quest:
                continue
            step_index = int(row["step"])
            if step_index >= len(quest["steps"]):
                continue
            step = quest["steps"][step_index]
            if step.get("choices") or step["kind"] != kind or step["target"] != target:
                continue
            progress = int(row["progress"]) + amount
            required = int(step.get("amount", 1))
            if progress < required:
                self.quests.update(user_id, row["quest_key"], step_index, progress)
                messages.append(f"📜 {quest['name']}: {progress}/{required}")
                continue
            messages.extend(self._advance(user_id, row["quest_key"], quest, step_index))
        return messages

    def choose(self, user_id: str, quest_key: str, choice_id: str) -> dict:
        p = self._require(user_id)
        row = self.quests.get(user_id, quest_key)
        quest = QUESTS.get(quest_key)
        if not row or not quest or row["status"] != "active":
            raise GameError("Nhiệm vụ không ở trạng thái có thể lựa chọn.")
        step_index = int(row["step"])
        step = quest["steps"][step_index]
        choices = step.get("choices") or []
        choice = next((c for c in choices if c["id"] == choice_id), None)
        if not choice:
            raise GameError("Lựa chọn nhiệm vụ không tồn tại.")
        condition = choice.get("condition", {})
        for stat, required in condition.items():
            if getattr(p, stat, 0) < required:
                raise GameError(f"Cần {STAT_DISPLAY_NAMES.get(stat, stat)} ≥ {required} để chọn phương án này.")
        effect = choice.get("effect", {})
        changes = []
        if effect.get("stones"):
            p.spirit_stones = max(0, p.spirit_stones + int(effect["stones"]))
            changes.append(f"{effect['stones']:+d} linh thạch")
        if effect.get("cultivation"):
            p.cultivation = max(0, p.cultivation + int(effect["cultivation"]))
            changes.append(f"{effect['cultivation']:+d} tu vi")
        if effect.get("fate"):
            p.fate = max(0, min(100, p.fate + int(effect["fate"])))
            changes.append(f"{effect['fate']:+d} mệnh số")
        if effect.get("insight"):
            p.insight = max(0, min(100, p.insight + int(effect["insight"])))
            changes.append(f"{effect['insight']:+d} ngộ tính")
        if effect.get("item"):
            self.inventory.add(user_id, effect["item"], 1)
            changes.append(f"nhận **{ITEMS.get(effect['item'], {}).get('name', effect['item'])}**")
        if effect.get("discover"):
            self.players.add_discovery(user_id, effect["discover"])
        if self.npc_service and effect.get("npc_affinity") is not None:
            self.npc_service.remember(user_id, quest["npc"], int(effect["npc_affinity"]), effect.get("flag"))
        next_step = choice.get("next_step")
        if next_step is None:
            messages = self._complete(user_id, quest_key, quest)
            status = self.status(user_id, quest_key)
        else:
            self.quests.update(user_id, quest_key, int(next_step), 0)
            self.players.save(p)
            self.players.add_history(user_id, "quest_choice", f"{quest_key}:{choice_id}")
            messages = [f"📜 {quest['name']}: {quest['steps'][int(next_step)]['label']}"]
            status = self.status(user_id, quest_key)
        return {"quest": quest, "choice": choice, "changes": changes, "messages": messages, "status": status}

    def _advance(self, user_id: str, quest_key: str, quest: dict, step_index: int) -> list[str]:
        next_step = step_index + 1
        if next_step >= len(quest["steps"]):
            self._complete(user_id, quest_key, quest)
            return [f"✨ Hoàn thành nhiệm vụ **{quest['name']}**!"]
        self.quests.update(user_id, quest_key, next_step, 0)
        return [f"📜 **{quest['name']}**: mục tiêu mới — {quest['steps'][next_step]['label']}"]

    def _complete(self, user_id: str, quest_key: str, quest: dict) -> list[str]:
        p = self._require(user_id)
        reward = quest.get("reward", {})
        p.spirit_stones += int(reward.get("stones", 0))
        p.cultivation += int(reward.get("cultivation", 0))
        p.fate = max(0, min(100, p.fate + int(reward.get("fate", 0))))
        p.insight = max(0, min(100, p.insight + int(reward.get("insight", 0))))
        self.players.save(p)
        self.quests.complete(user_id, quest_key)
        self.players.add_history(user_id, "quest_complete", quest_key)
        if self.npc_service:
            self.npc_service.remember(user_id, quest["npc"], int(reward.get("npc_affinity", 2)), "completed_" + quest_key)
        return [f"🎁 +{reward.get('stones', 0)} linh thạch", f"✨ +{reward.get('cultivation', 0)} tu vi"]
