from __future__ import annotations

from game.content.npcs import NPCS
from game.repositories.npc_repository import NPCRepository
from game.services.errors import GameError


class NPCService:
    def __init__(self, players, quests, npc_repository: NPCRepository):
        self.players = players
        self.quests = quests
        self.relationships = npc_repository

    def list_npcs(self, user_id: str) -> list[dict]:
        p = self.players.get(user_id)
        if not p:
            raise GameError("Ngươi chưa bước lên con đường tu hành.")
        result = []
        for key, npc in NPCS.items():
            if npc["zone"] == p.explore_zone:
                rel = self.relationships.get(user_id, key)
                result.append({"key": key, **npc, "affinity": rel["affinity"], "interactions": rel["interactions"]})
        return result

    def talk(self, user_id: str, npc_key: str) -> dict:
        p = self.players.get(user_id)
        if not p:
            raise GameError("Ngươi chưa bước lên con đường tu hành.")
        npc = NPCS.get(npc_key)
        if not npc:
            raise GameError("Không tìm thấy NPC này.")
        if npc["zone"] != p.explore_zone and p.realm_index < 3:
            raise GameError("NPC này không ở khu vực hiện tại.")
        rel = self.relationships.get(user_id, npc_key)
        available = []
        for quest_key in npc.get("quests", []):
            row = self.quests.quests.get(user_id, quest_key)
            if not row:
                available.append(quest_key)
        greeting = npc.get("greeting", "")
        if rel["affinity"] >= 5:
            greeting = npc.get("friendly_greeting", greeting)
        elif rel["affinity"] <= -5:
            greeting = npc.get("hostile_greeting", greeting)
        elif rel["interactions"] > 0:
            greeting = npc.get("return_greeting", greeting)
        rel = self.remember(user_id, npc_key, 0)
        return {"key": npc_key, "npc": npc, "quests": available, "relationship": rel, "greeting": greeting}

    def remember(self, user_id: str, npc_key: str, affinity_delta: int = 0, flag: str | None = None, value=True) -> dict:
        if npc_key not in NPCS:
            raise GameError("Không tìm thấy NPC này.")
        rel = self.relationships.get(user_id, npc_key)
        flags = dict(rel.get("flags") or {})
        if flag:
            flags[flag] = value
        return self.relationships.save(
            user_id, npc_key,
            max(-100, min(100, int(rel["affinity"]) + int(affinity_delta))),
            flags,
            int(rel["interactions"]) + 1,
        )

    def relationship(self, user_id: str, npc_key: str) -> dict:
        if npc_key not in NPCS:
            raise GameError("Không tìm thấy NPC này.")
        return self.relationships.get(user_id, npc_key)
