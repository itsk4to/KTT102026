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


def migrate_4_to_5(db) -> None:
    db.execute("""CREATE TABLE IF NOT EXISTS pending_exploration_events (
        user_id TEXT PRIMARY KEY,
        event_key TEXT NOT NULL,
        zone_key TEXT NOT NULL,
        payload TEXT NOT NULL,
        created_at INTEGER NOT NULL
    )""")
    _set_version(db, 5)


def migrate_5_to_6(db) -> None:
    # v6 added immersive exploration/quest/world-event persistence.
    db.execute("""CREATE TABLE IF NOT EXISTS player_quests (
        user_id TEXT NOT NULL, quest_key TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active',
        step INTEGER NOT NULL DEFAULT 0, progress INTEGER NOT NULL DEFAULT 0,
        started_at INTEGER NOT NULL, completed_at INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (user_id, quest_key)
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS world_events (
        event_key TEXT PRIMARY KEY, zone_key TEXT NOT NULL, progress INTEGER NOT NULL DEFAULT 0,
        target INTEGER NOT NULL, expires_at INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'active', created_at INTEGER NOT NULL
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS world_event_contributors (
        event_key TEXT NOT NULL, user_id TEXT NOT NULL, created_at INTEGER NOT NULL,
        PRIMARY KEY (event_key, user_id)
    )""")
    _set_version(db, 6)


def migrate_6_to_7(db) -> None:
    db.execute("""CREATE TABLE IF NOT EXISTS npc_relationships (
        user_id TEXT NOT NULL, npc_key TEXT NOT NULL, affinity INTEGER NOT NULL DEFAULT 0,
        flags TEXT NOT NULL DEFAULT '{}', interactions INTEGER NOT NULL DEFAULT 0,
        last_interaction INTEGER NOT NULL DEFAULT 0, PRIMARY KEY (user_id, npc_key)
    )""")
    _set_version(db, 7)

def migrate_7_to_8(db) -> None:
    # Sect expansion: persistent tower progress and daily mission state.
    _set_version(db, 8)


def migrate_8_to_9(db) -> None:
    # Per-member mission claim state and global reputation.
    if "claimed" not in {r["name"] for r in db.fetchall("PRAGMA table_info(mission_progress)")}:
        db.execute("ALTER TABLE mission_progress ADD COLUMN claimed INTEGER NOT NULL DEFAULT 0")
    if "reputation" not in {r["name"] for r in db.fetchall("PRAGMA table_info(players)")}:
        db.execute("ALTER TABLE players ADD COLUMN reputation INTEGER NOT NULL DEFAULT 0")
    _set_version(db, 9)


def migrate_9_to_10(db) -> None:
    cols = {r["name"] for r in db.fetchall("PRAGMA table_info(market_listings)")}
    if "unit_price" not in cols:
        db.execute("ALTER TABLE market_listings ADD COLUMN unit_price INTEGER NOT NULL DEFAULT 0")
    # Legacy v9 listings stored only the stack total in price. Preserve them
    # while making the per-unit price explicit for all future listings.
    db.execute("UPDATE market_listings SET unit_price = CASE WHEN quantity > 0 THEN MAX(1, price / quantity) ELSE MAX(1, price) END WHERE unit_price <= 0")
    _set_version(db, 10)


def migrate_10_to_11(db) -> None:
    cols = {r["name"] for r in db.fetchall("PRAGMA table_info(players)")}
    if "breakthrough_recovery_until" not in cols:
        db.execute("ALTER TABLE players ADD COLUMN breakthrough_recovery_until INTEGER NOT NULL DEFAULT 0")
    _set_version(db, 11)


def migrate_11_to_12(db) -> None:
    cols = {r["name"] for r in db.fetchall("PRAGMA table_info(redeem_codes)")}
    if "enabled" not in cols:
        db.execute("ALTER TABLE redeem_codes ADD COLUMN enabled INTEGER NOT NULL DEFAULT 1")
    _set_version(db, 12)

def migrate_12_to_13(db) -> None:
    db.execute("""CREATE TABLE IF NOT EXISTS pvp_matches (
        match_id TEXT PRIMARY KEY,
        payload TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        created_at INTEGER NOT NULL
    )""")
    _set_version(db, 13)

def migrate_13_to_14(db) -> None:
    # Persist one active timed Secret Realm session per player.
    db.execute("""CREATE TABLE IF NOT EXISTS secret_realm_sessions (
        user_id TEXT PRIMARY KEY,
        realm_key TEXT NOT NULL,
        cycle_started_at INTEGER NOT NULL,
        claims INTEGER NOT NULL DEFAULT 0
    )""")
    _set_version(db, 14)


def migrate_14_to_15(db) -> None:
    # Keep admin authentication valid for one day, including across bot restarts.
    db.execute("""CREATE TABLE IF NOT EXISTS admin_sessions (
        user_id TEXT PRIMARY KEY,
        created_at INTEGER NOT NULL,
        expires_at INTEGER NOT NULL
    )""")
    _set_version(db, 15)


def migrate_15_to_16(db) -> None:
    # Persistent pity for failed breakthroughs and durable daily/weekly missions.
    cols = {r["name"] for r in db.fetchall("PRAGMA table_info(players)")}
    if "breakthrough_pity" not in cols:
        db.execute("ALTER TABLE players ADD COLUMN breakthrough_pity INTEGER NOT NULL DEFAULT 0")
    db.execute("""CREATE TABLE IF NOT EXISTS player_mission_progress (
        user_id TEXT NOT NULL, mission_id TEXT NOT NULL, period_key TEXT NOT NULL,
        progress INTEGER NOT NULL DEFAULT 0, claimed INTEGER NOT NULL DEFAULT 0,
        updated_at INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (user_id, mission_id, period_key)
    )""")
    _set_version(db, 16)


_MIGRATIONS = {
    0: migrate_0_to_1,
    1: migrate_1_to_2,
    2: migrate_2_to_3,
    3: migrate_3_to_4,
    4: migrate_4_to_5,
    5: migrate_5_to_6,
    6: migrate_6_to_7,
    7: migrate_7_to_8,
    8: migrate_8_to_9,
    9: migrate_9_to_10,
    10: migrate_10_to_11,
    11: migrate_11_to_12,
    12: migrate_12_to_13,
    13: migrate_13_to_14,
    14: migrate_14_to_15,
    15: migrate_15_to_16,
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
