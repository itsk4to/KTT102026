from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class StatusEffect:
    effect_id: str
    duration: int
    potency: float = 1.0


@dataclass
class Encounter:
    player_id: str
    enemy_name: str
    enemy_hp: int
    enemy_max_hp: int
    enemy_attack: int
    enemy_defense: int
    player_hp: int
    player_max_hp: int
    is_boss: bool = False
    is_elite: bool = False
    player_statuses: list[StatusEffect] = field(default_factory=list)
    enemy_statuses: list[StatusEffect] = field(default_factory=list)
    log: list[str] = field(default_factory=list)
    finished: bool = False
    victory: bool | None = None

    def to_dict(self) -> dict:
        return {
            "player_id": self.player_id,
            "enemy_name": self.enemy_name,
            "enemy_hp": self.enemy_hp,
            "enemy_max_hp": self.enemy_max_hp,
            "enemy_attack": self.enemy_attack,
            "enemy_defense": self.enemy_defense,
            "player_hp": self.player_hp,
            "player_max_hp": self.player_max_hp,
            "is_boss": self.is_boss,
            "is_elite": self.is_elite,
            "player_statuses": [s.__dict__ for s in self.player_statuses],
            "enemy_statuses": [s.__dict__ for s in self.enemy_statuses],
            "log": list(self.log),
            "finished": self.finished,
            "victory": self.victory,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Encounter":
        ps = [StatusEffect(**s) if isinstance(s, dict) else s for s in data.get("player_statuses", [])]
        es = [StatusEffect(**s) if isinstance(s, dict) else s for s in data.get("enemy_statuses", [])]
        return cls(
            player_id=data["player_id"],
            enemy_name=data["enemy_name"],
            enemy_hp=int(data["enemy_hp"]),
            enemy_max_hp=int(data["enemy_max_hp"]),
            enemy_attack=int(data["enemy_attack"]),
            enemy_defense=int(data["enemy_defense"]),
            player_hp=int(data["player_hp"]),
            player_max_hp=int(data["player_max_hp"]),
            is_boss=bool(data.get("is_boss")),
            is_elite=bool(data.get("is_elite")),
            player_statuses=ps,
            enemy_statuses=es,
            log=list(data.get("log", [])),
            finished=bool(data.get("finished")),
            victory=data.get("victory"),
        )
