from __future__ import annotations

from game.content.dao_paths import DAO_PATHS, DAO_STAGE_THRESHOLD
from game.repositories.player_repository import PlayerRepository
from game.rules.dao_rules import stage_from_insight, stage_name
from game.services.errors import GameError


class DaoService:
    def __init__(self, players: PlayerRepository):
        self.players = players

    def choose(self, user_id: str, dao_type: str) -> dict:
        if dao_type not in DAO_PATHS:
            raise GameError("Đạo không hợp lệ. Chọn: " + ", ".join(DAO_PATHS))
        p = self.players.get(user_id)
        if not p:
            raise GameError("Ngươi chưa khai đạo.")
        if p.dao_type and p.dao_type != dao_type:
            raise GameError(f"Đã chọn **{DAO_PATHS[p.dao_type]['name']}**. Không đổi được.")
        p.dao_type = dao_type
        p.dao_stage = stage_from_insight(p.dao_insight)
        self.players.save(p)
        return {"dao": DAO_PATHS[dao_type], "stage": stage_name(p.dao_stage), "player": p}

    def info(self, user_id: str) -> dict | None:
        p = self.players.get(user_id)
        if not p or not p.dao_type:
            return None
        return {
            "dao_type": p.dao_type,
            "dao": DAO_PATHS[p.dao_type],
            "insight": p.dao_insight,
            "stage": p.dao_stage,
            "stage_name": stage_name(p.dao_stage),
            "next_threshold": (p.dao_stage + 1) * DAO_STAGE_THRESHOLD,
        }

    def gain_insight(self, user_id: str, amount: int = 1) -> dict:
        p = self.players.get(user_id)
        if not p or not p.dao_type:
            raise GameError("Chưa chọn Đạo.")
        p.dao_insight += amount
        p.dao_stage = stage_from_insight(p.dao_insight)
        self.players.save(p)
        return self.info(user_id)  # type: ignore
