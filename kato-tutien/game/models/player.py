from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Player:
    user_id: str
    display_name: str = ""
    path: str = "tien"  # tien | ma
    realm_index: int = 0
    realm_layer: int = 1
    cultivation: int = 0
    spirit_stones: int = 1000
    root: int = 50
    insight: int = 50
    luck: int = 50
    fate: int = 50
    mind: int = 50
    destiny: str = ""
    talent: str = ""
    hp: int = 100
    max_hp: int = 100
    attack: int = 10
    defense: int = 5
    injury: int = 0
    lifespan: int = 100
    dao_type: str = ""
    dao_stage: int = 0
    dao_insight: int = 0
    sect_id: str | None = None
    explore_zone: str = "hoangnguyen"
    loadout: dict[str, str | None] = field(default_factory=dict)
    equipped: str = ""
    last_cultivate: int = 0
    last_explore: int = 0
    last_hunt: int = 0
    last_daily: int = 0
    daily_streak: int = 0
    be_quan_active: int = 0
    be_quan_last_tick: int = 0
    be_quan_prepaid: int = 0
    trial_floor: int = 0
    trial_attempts: int = 0
    trial_day: str = ""
    ascension_floor: int = 0
    created_at: int = 0

    @classmethod
    def from_row(cls, row) -> "Player":
        data = dict(row)
        raw = data.get("loadout") or "{}"
        try:
            loadout = json.loads(raw) if isinstance(raw, str) else (raw or {})
        except json.JSONDecodeError:
            loadout = {}
        data["loadout"] = loadout
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore
        return cls(**{k: v for k, v in data.items() if k in known})

    def loadout_json(self) -> str:
        return json.dumps(self.loadout or {}, ensure_ascii=False)

    def to_public(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "name": self.display_name,
            "path": self.path,
            "realm_index": self.realm_index,
            "realm_layer": self.realm_layer,
            "cultivation": self.cultivation,
            "dao_type": self.dao_type,
            "dao_stage": self.dao_stage,
        }
