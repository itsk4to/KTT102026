from __future__ import annotations

import random
import time

from game.content.world_events import WORLD_EVENTS
from game.repositories.world_repository import WorldRepository
from game.services.errors import GameError


class WorldService:
    def __init__(self, players, world: WorldRepository, rng: random.Random | None = None):
        self.players = players
        self.world = world
        self.rng = rng or random.Random()

    def active(self) -> list[dict]:
        return self.world.active()

    def maybe_spawn(self, zone_key: str) -> dict | None:
        if self.active() or self.rng.random() >= 0.03:
            return None
        candidates = [e for e in WORLD_EVENTS.values() if e["zone"] == zone_key]
        if not candidates:
            return None
        event = self.rng.choice(candidates)
        key = next(k for k, v in WORLD_EVENTS.items() if v is event)
        self.world.create(key, zone_key, int(event["target"]), int(time.time()) + int(event["duration"]))
        return {"key": key, **event}

    def contribute(self, user_id: str, event_key: str) -> dict:
        p = self.players.get(user_id)
        if not p:
            raise GameError("Ngươi chưa bước lên con đường tu hành.")
        event = WORLD_EVENTS.get(event_key)
        row = self.world.get(event_key)
        if not event or not row:
            raise GameError("Sự kiện thế giới đã kết thúc hoặc không tồn tại.")
        now = int(time.time())
        if row["status"] != "active" or int(row["expires_at"]) <= now:
            if row["status"] == "active":
                self.world.finish(event_key)
            raise GameError("Sự kiện thế giới đã kết thúc.")
        if p.explore_zone != row["zone_key"]:
            raise GameError(f"Hãy đến **{row['zone_key']}** để tham gia sự kiện này.")
        if self.world.contributed(event_key, user_id):
            raise GameError("Ngươi đã góp sức vào sự kiện này rồi.")
        self.world.contribute(event_key, user_id)
        p.spirit_stones += int(event["reward"]["stones"])
        p.cultivation += int(event["reward"]["cultivation"])
        self.players.save(p)
        self.players.add_history(user_id, "world_event", event_key)
        current = row["progress"] + 1
        finished = current >= row["target"]
        if finished:
            self.world.finish(event_key)
        return {"event": event, "progress": current, "target": row["target"], "finished": finished, "player": p}
