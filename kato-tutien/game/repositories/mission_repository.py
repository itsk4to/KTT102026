from __future__ import annotations

from game.database.connection import Database


class MissionRepository:
    def __init__(self, db: Database):
        self.db = db

    def get(self, user_id: str, sect_id: str, mission_key: str, day_key: str):
        row = self.db.fetchone(
            "SELECT * FROM mission_progress WHERE user_id=? AND sect_id=? AND mission_key=? AND day_key=?",
            (user_id, sect_id, mission_key, day_key),
        )
        return dict(row) if row else None

    def upsert(self, user_id: str, sect_id: str, mission_key: str, progress: int, day_key: str, claimed: bool) -> None:
        self.db.execute(
            "INSERT INTO mission_progress(user_id,sect_id,mission_key,progress,day_key,claimed) "
            "VALUES(?,?,?,?,?,?) "
            "ON CONFLICT(user_id,sect_id,mission_key,day_key) DO UPDATE SET progress=excluded.progress",
            (user_id, sect_id, mission_key, progress, day_key, 1 if claimed else 0),
        )

    def claim_once(self, user_id: str, sect_id: str, mission_key: str, day_key: str) -> bool:
        return self.db.execute(
            "UPDATE mission_progress SET claimed=1 "
            "WHERE user_id=? AND sect_id=? AND mission_key=? AND day_key=? AND claimed=0",
            (user_id, sect_id, mission_key, day_key),
        ).rowcount == 1
