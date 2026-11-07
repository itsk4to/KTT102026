"""Per-guild runtime settings — configured in Discord, not only via env."""
from __future__ import annotations

from typing import Any

import config
from game.database.connection import Database

# Canonical keys stored in guild_settings.value as text (usually snowflake IDs).
KEY_PRISON_ROLE_ID = "prison_role_id"
KEY_PRISON_CHANNEL_ID = "prison_channel_id"
KEY_PRISON_ANNOUNCE_CHANNEL_ID = "prison_announce_channel_id"
KEY_MOD_LOG_CHANNEL_ID = "mod_log_channel_id"
KEY_PRISON_COOLDOWN_SECONDS = "prison_cooldown_seconds"
KEY_PRISON_MAX_REQUIRED_STONES = "prison_max_required_stones"


class GuildSettingsRepository:
    def __init__(self, db: Database):
        self.db = db

    def get(self, guild_id: str | int, key: str) -> str | None:
        row = self.db.fetchone(
            "SELECT value FROM guild_settings WHERE guild_id=? AND key=?",
            (str(guild_id), str(key)),
        )
        if row is None:
            return None
        value = row["value"]
        return None if value is None else str(value)

    def get_int(self, guild_id: str | int, key: str, default: int = 0) -> int:
        raw = self.get(guild_id, key)
        if raw is None or raw == "":
            return int(default)
        try:
            return int(raw)
        except ValueError:
            return int(default)

    def set(self, guild_id: str | int, key: str, value: str | int | None) -> None:
        if value is None or value == "" or value == 0:
            self.db.execute(
                "DELETE FROM guild_settings WHERE guild_id=? AND key=?",
                (str(guild_id), str(key)),
            )
            return
        self.db.execute(
            """INSERT INTO guild_settings(guild_id, key, value)
               VALUES(?,?,?)
               ON CONFLICT(guild_id, key) DO UPDATE SET value=excluded.value""",
            (str(guild_id), str(key), str(value)),
        )

    def all_for_guild(self, guild_id: str | int) -> dict[str, str]:
        rows = self.db.fetchall(
            "SELECT key, value FROM guild_settings WHERE guild_id=?",
            (str(guild_id),),
        )
        return {str(row["key"]): str(row["value"]) for row in rows}


def resolve_prison_settings(db: Database, guild_id: str | int) -> dict[str, int]:
    """Guild DB settings override env defaults from config.py."""
    repo = GuildSettingsRepository(db)
    return {
        "prison_role_id": repo.get_int(guild_id, KEY_PRISON_ROLE_ID, config.PRISON_ROLE_ID),
        "prison_channel_id": repo.get_int(guild_id, KEY_PRISON_CHANNEL_ID, config.PRISON_CHANNEL_ID),
        "prison_announce_channel_id": repo.get_int(
            guild_id, KEY_PRISON_ANNOUNCE_CHANNEL_ID, config.PRISON_ANNOUNCE_CHANNEL_ID
        ),
        "prison_cooldown_seconds": repo.get_int(
            guild_id, KEY_PRISON_COOLDOWN_SECONDS, config.PRISON_COOLDOWN_SECONDS
        ) or config.PRISON_COOLDOWN_SECONDS,
        "prison_max_required_stones": repo.get_int(
            guild_id, KEY_PRISON_MAX_REQUIRED_STONES, config.PRISON_MAX_REQUIRED_STONES
        ) or config.PRISON_MAX_REQUIRED_STONES,
    }


def resolve_mod_log_channel_id(db: Database, guild_id: str | int) -> int:
    repo = GuildSettingsRepository(db)
    return repo.get_int(guild_id, KEY_MOD_LOG_CHANNEL_ID, config.MOD_LOG_CHANNEL_ID)


def settings_summary(db: Database, guild_id: str | int) -> dict[str, Any]:
    prison = resolve_prison_settings(db, guild_id)
    return {
        **prison,
        "mod_log_channel_id": resolve_mod_log_channel_id(db, guild_id),
        "source": GuildSettingsRepository(db).all_for_guild(guild_id),
    }
