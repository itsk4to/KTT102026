from __future__ import annotations

from game.database.connection import Database
from game.models.player import Player


class PlayerRepository:
    def __init__(self, db: Database):
        self.db = db

    def transaction(self):
        return self.db.transaction()

    def get(self, user_id: str) -> Player | None:
        row = self.db.fetchone("SELECT * FROM players WHERE user_id=?", (user_id,))
        return Player.from_row(row) if row else None

    def exists(self, user_id: str) -> bool:
        row = self.db.fetchone("SELECT 1 FROM players WHERE user_id=?", (user_id,))
        return row is not None

    def create(self, player: Player) -> None:
        self.db.execute(
            """INSERT INTO players (
                user_id, display_name, path, realm_index, realm_layer, cultivation,
                spirit_stones, root, insight, luck, fate, mind, reputation, destiny, talent,
                hp, max_hp, attack, defense, injury, lifespan,
                dao_type, dao_stage, dao_insight, sect_id, explore_zone,
                loadout, equipped, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                player.user_id, player.display_name, player.path,
                player.realm_index, player.realm_layer, player.cultivation,
                player.spirit_stones, player.root, player.insight, player.luck,
                player.fate, player.mind, player.reputation, player.destiny, player.talent,
                player.hp, player.max_hp, player.attack, player.defense,
                player.injury, player.lifespan, player.dao_type, player.dao_stage,
                player.dao_insight, player.sect_id, player.explore_zone,
                player.loadout_json(), player.equipped, player.created_at,
            ),
        )

    def save(self, player: Player) -> None:
        self.db.execute(
            """UPDATE players SET
                display_name=?, path=?, realm_index=?, realm_layer=?, cultivation=?,
                spirit_stones=?, root=?, insight=?, luck=?, fate=?, mind=?, reputation=?,
                destiny=?, talent=?, hp=?, max_hp=?, attack=?, defense=?,
                injury=?, lifespan=?, dao_type=?, dao_stage=?, dao_insight=?,
                sect_id=?, explore_zone=?, loadout=?, equipped=?,
                last_cultivate=?, last_explore=?, last_hunt=?, last_daily=?,
                daily_streak=?, be_quan_active=?, be_quan_last_tick=?, be_quan_prepaid=?,
                trial_floor=?, trial_attempts=?, trial_day=?, ascension_floor=?
            WHERE user_id=?""",
            (
                player.display_name, player.path, player.realm_index, player.realm_layer,
                player.cultivation, player.spirit_stones, player.root, player.insight,
                player.luck, player.fate, player.mind, player.reputation, player.destiny, player.talent,
                player.hp, player.max_hp, player.attack, player.defense, player.injury,
                player.lifespan, player.dao_type, player.dao_stage, player.dao_insight,
                player.sect_id, player.explore_zone, player.loadout_json(), player.equipped,
                player.last_cultivate, player.last_explore, player.last_hunt, player.last_daily,
                player.daily_streak, player.be_quan_active, player.be_quan_last_tick,
                player.be_quan_prepaid, player.trial_floor, player.trial_attempts,
                player.trial_day, player.ascension_floor, player.user_id,
            ),
        )


    def count(self) -> int:
        row = self.db.fetchone("SELECT COUNT(*) AS c FROM players")
        return int(row["c"]) if row else 0

    def leaderboard(self, limit: int = 10, path: str | None = None) -> list[Player]:
        if path:
            rows = self.db.fetchall(
                "SELECT * FROM players WHERE path=? ORDER BY realm_index DESC, realm_layer DESC, cultivation DESC LIMIT ?",
                (path, limit),
            )
        else:
            rows = self.db.fetchall(
                "SELECT * FROM players ORDER BY realm_index DESC, realm_layer DESC, cultivation DESC LIMIT ?",
                (limit,),
            )
        return [Player.from_row(r) for r in rows]

    def add_history(self, user_id: str, event_type: str, detail: str = "") -> None:
        import time
        self.db.execute(
            "INSERT INTO player_history(user_id, event_type, detail, created_at) VALUES(?,?,?,?)",
            (user_id, event_type, detail, int(time.time())),
        )

    def get_mastery(self, user_id: str, technique_id: str) -> dict | None:
        row = self.db.fetchone(
            "SELECT * FROM technique_mastery WHERE user_id=? AND technique_id=?",
            (user_id, technique_id),
        )
        return dict(row) if row else None

    def upsert_mastery(self, user_id: str, technique_id: str, mastery: int, stage: str) -> None:
        self.db.execute(
            """INSERT INTO technique_mastery(user_id, technique_id, mastery, stage)
               VALUES(?,?,?,?)
               ON CONFLICT(user_id, technique_id) DO UPDATE SET mastery=excluded.mastery, stage=excluded.stage""",
            (user_id, technique_id, mastery, stage),
        )

    def has_discovery(self, user_id: str, key: str) -> bool:
        row = self.db.fetchone(
            "SELECT 1 FROM discoveries WHERE user_id=? AND event_key=?",
            (user_id, key),
        )
        return row is not None

    def add_discovery(self, user_id: str, key: str) -> bool:
        if self.has_discovery(user_id, key):
            return False
        self.db.execute(
            "INSERT INTO discoveries(user_id, event_key) VALUES(?,?)",
            (user_id, key),
        )
        return True
