"""Versioned, idempotent SQLite migrations."""
from __future__ import annotations

from game.database.schema import SCHEMA_VERSION, ensure_schema


def _version(db) -> int:
    row = db.fetchone("SELECT value FROM schema_meta WHERE key='version'")
    return int(row["value"]) if row else 0


def _set_version(db, version: int) -> None:
    db.execute(
        "INSERT OR REPLACE INTO schema_meta(key, value) VALUES('version', ?)",
        (str(version),),
    )


def migrate_0_to_1(db) -> None:
    # Base tables are created by ensure_schema().
    _set_version(db, 1)


def migrate_1_to_2(db) -> None:
    # Historical v2 introduced player history and market/sect tables. The
    # repairable canonical schema already creates them when missing.
    _set_version(db, 2)


def migrate_2_to_3(db) -> None:
    # Historical v3 kept the same data model but added the current gameplay
    # columns. Missing player columns are repaired by ensure_schema().
    _set_version(db, 3)


def migrate_3_to_4(db) -> None:
    # v4 adds durable sect role history. CREATE IF NOT EXISTS makes this safe
    # for both fresh and already-migrated databases.
    db.execute(
        """CREATE TABLE IF NOT EXISTS sect_role_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sect_id TEXT NOT NULL,
            actor_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            old_role TEXT NOT NULL,
            new_role TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )"""
    )
    _set_version(db, 4)


_MIGRATIONS = {
    0: migrate_0_to_1,
    1: migrate_1_to_2,
    2: migrate_2_to_3,
    3: migrate_3_to_4,
}


def run_migrations(db) -> int:
    ensure_schema(db)
    current = _version(db)
    while current < SCHEMA_VERSION:
        step = _MIGRATIONS[current]
        with db.transaction():
            step(db)
        current += 1
    return current
