from __future__ import annotations

import random
import time

from game.content.talents import DESTINIES, PATH_TALENTS
from game.models.player import Player
from game.repositories.player_repository import PlayerRepository
from game.rules.cultivation_rules import realm_text
from game.services.errors import GameError
from config import STARTING_STONES


class PlayerService:
    def __init__(self, players: PlayerRepository, rng: random.Random | None = None):
        self.players = players
        self.rng = rng or random.Random()

    def get(self, user_id: str) -> Player:
        p = self.players.get(user_id)
        if not p:
            raise GameError("Ngươi chưa bước lên con đường tu hành. Dùng `.tutien` để bắt đầu.")
        return p

    def exists(self, user_id: str) -> bool:
        return self.players.exists(user_id)

    def create(self, user_id: str, display_name: str, path: str) -> Player:
        if path not in ("tien", "ma"):
            raise GameError("Chọn Tiên đạo (`tien`) hoặc Ma đạo (`ma`).")
        if self.players.exists(user_id):
            raise GameError("Ngươi đã có nhân vật rồi.")
        talents = PATH_TALENTS.get(path, ["Thanh Tâm"])
        player = Player(
            user_id=user_id,
            display_name=display_name or user_id,
            path=path,
            root=self.rng.randint(35, 92),
            insight=self.rng.randint(35, 92),
            luck=self.rng.randint(35, 92),
            fate=self.rng.randint(35, 92),
            mind=self.rng.randint(35, 92),
            destiny=self.rng.choice(DESTINIES),
            talent=self.rng.choice(talents),
            spirit_stones=STARTING_STONES,
            hp=100,
            max_hp=100,
            attack=10 + self.rng.randint(0, 5),
            defense=5 + self.rng.randint(0, 3),
            created_at=int(time.time()),
        )
        self.players.create(player)
        self.players.add_history(user_id, "create", f"path={path}")
        return player

    def info_text(self, user_id: str) -> dict:
        p = self.get(user_id)
        return {
            "player": p,
            "realm": realm_text(p.realm_index, p.realm_layer),
        }

    def leaderboard(self, limit: int = 10, path: str | None = None) -> list[Player]:
        return self.players.leaderboard(limit, path)
