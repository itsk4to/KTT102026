"""Schema definitions and schema-repair helpers."""
from __future__ import annotations

SCHEMA_VERSION = 8

DDL = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS players (
    user_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL DEFAULT '',
    path TEXT NOT NULL DEFAULT 'tien',
    realm_index INTEGER NOT NULL DEFAULT 0,
    realm_layer INTEGER NOT NULL DEFAULT 1,
    cultivation INTEGER NOT NULL DEFAULT 0,
    spirit_stones INTEGER NOT NULL DEFAULT 1000,
    root INTEGER NOT NULL DEFAULT 50,
    insight INTEGER NOT NULL DEFAULT 50,
    luck INTEGER NOT NULL DEFAULT 50,
    fate INTEGER NOT NULL DEFAULT 50,
    mind INTEGER NOT NULL DEFAULT 50,
    destiny TEXT NOT NULL DEFAULT '',
    talent TEXT NOT NULL DEFAULT '',
    hp INTEGER NOT NULL DEFAULT 100,
    max_hp INTEGER NOT NULL DEFAULT 100,
    attack INTEGER NOT NULL DEFAULT 10,
    defense INTEGER NOT NULL DEFAULT 5,
    injury INTEGER NOT NULL DEFAULT 0,
    lifespan INTEGER NOT NULL DEFAULT 100,
    dao_type TEXT NOT NULL DEFAULT '',
    dao_stage INTEGER NOT NULL DEFAULT 0,
    dao_insight INTEGER NOT NULL DEFAULT 0,
    sect_id TEXT,
    explore_zone TEXT NOT NULL DEFAULT 'hoangnguyen',
    loadout TEXT NOT NULL DEFAULT '{}',
    equipped TEXT NOT NULL DEFAULT '',
    last_cultivate INTEGER NOT NULL DEFAULT 0,
    last_explore INTEGER NOT NULL DEFAULT 0,
    last_hunt INTEGER NOT NULL DEFAULT 0,
    last_daily INTEGER NOT NULL DEFAULT 0,
    daily_streak INTEGER NOT NULL DEFAULT 0,
    be_quan_active INTEGER NOT NULL DEFAULT 0,
    be_quan_last_tick INTEGER NOT NULL DEFAULT 0,
    be_quan_prepaid INTEGER NOT NULL DEFAULT 0,
    trial_floor INTEGER NOT NULL DEFAULT 0,
    trial_attempts INTEGER NOT NULL DEFAULT 0,
    trial_day TEXT NOT NULL DEFAULT '',
    ascension_floor INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS inventory (
    user_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, item_id)
);

CREATE TABLE IF NOT EXISTS discoveries (
    user_id TEXT NOT NULL,
    event_key TEXT NOT NULL,
    PRIMARY KEY (user_id, event_key)
);

CREATE TABLE IF NOT EXISTS technique_mastery (
    user_id TEXT NOT NULL,
    technique_id TEXT NOT NULL,
    mastery INTEGER NOT NULL DEFAULT 1,
    stage TEXT NOT NULL DEFAULT 'Nhập môn',
    PRIMARY KEY (user_id, technique_id)
);

CREATE TABLE IF NOT EXISTS market_listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id TEXT NOT NULL,
    item_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price INTEGER NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sects (
    sect_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    owner_id TEXT NOT NULL,
    level INTEGER NOT NULL DEFAULT 1,
    exp INTEGER NOT NULL DEFAULT 0,
    treasury INTEGER NOT NULL DEFAULT 0,
    linh_mach_level INTEGER NOT NULL DEFAULT 0,
    created_at INTEGER NOT NULL DEFAULT 0,
    tower_floor INTEGER NOT NULL DEFAULT 0,
    mission_day TEXT NOT NULL DEFAULT '',
    mission_key TEXT NOT NULL DEFAULT '',
    mission_progress INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sect_members (
    sect_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'Ngoại Môn Đệ Tử',
    contribution INTEGER NOT NULL DEFAULT 0,
    joined_at INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (sect_id, user_id)
);

CREATE TABLE IF NOT EXISTS sect_applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sect_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    message TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    created_at INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sect_invitations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sect_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    inviter_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sect_role_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sect_id TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    old_role TEXT NOT NULL,
    new_role TEXT NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS pvp_challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    challenger_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    bet_type TEXT NOT NULL DEFAULT 'stones',
    item_id TEXT,
    amount INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS dao_lu (
    user_a TEXT NOT NULL,
    user_b TEXT NOT NULL,
    intimacy INTEGER NOT NULL DEFAULT 0,
    last_song_tu INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_a, user_b)
);

CREATE TABLE IF NOT EXISTS dao_lu_requests (
    requester_id TEXT PRIMARY KEY,
    target_id TEXT NOT NULL,
    created_at INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS redeem_codes (
    code TEXT PRIMARY KEY,
    reward_stones INTEGER NOT NULL DEFAULT 0,
    reward_item TEXT,
    reward_qty INTEGER NOT NULL DEFAULT 0,
    max_uses INTEGER NOT NULL DEFAULT 1,
    used_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS heavenly_rules (
    rule_key TEXT PRIMARY KEY,
    rule_text TEXT NOT NULL DEFAULT '',
    enabled INTEGER NOT NULL DEFAULT 1,
    updated_by TEXT NOT NULL DEFAULT '',
    updated_at INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS code_redemptions (
    code TEXT NOT NULL,
    user_id TEXT NOT NULL,
    redeemed_at INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (code, user_id)
);

CREATE TABLE IF NOT EXISTS admin_users (
    user_id TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS admin_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    target_id TEXT,
    details TEXT NOT NULL DEFAULT '',
    created_at INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS mission_progress (
    user_id TEXT NOT NULL,
    sect_id TEXT NOT NULL,
    mission_key TEXT NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0,
    day_key TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (user_id, sect_id, mission_key, day_key)
);

CREATE TABLE IF NOT EXISTS player_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    detail TEXT NOT NULL DEFAULT '',
    created_at INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS pending_exploration_events (
    user_id TEXT PRIMARY KEY,
    event_key TEXT NOT NULL,
    zone_key TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS player_quests (
    user_id TEXT NOT NULL,
    quest_key TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    step INTEGER NOT NULL DEFAULT 0,
    progress INTEGER NOT NULL DEFAULT 0,
    started_at INTEGER NOT NULL,
    completed_at INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, quest_key)
);

CREATE TABLE IF NOT EXISTS world_events (
    event_key TEXT PRIMARY KEY,
    zone_key TEXT NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0,
    target INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS world_event_contributors (
    event_key TEXT NOT NULL,
    user_id TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    PRIMARY KEY (event_key, user_id)
);

CREATE TABLE IF NOT EXISTS npc_relationships (
    user_id TEXT NOT NULL,
    npc_key TEXT NOT NULL,
    affinity INTEGER NOT NULL DEFAULT 0,
    flags TEXT NOT NULL DEFAULT '{}',
    interactions INTEGER NOT NULL DEFAULT 0,
    last_interaction INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, npc_key)
);
"""

# Known columns from the canonical v4 schema. This allows old SQLite files to
# be repaired safely instead of only bumping a version flag.
_REQUIRED_COLUMNS = {
    "players": {
        "display_name": "TEXT NOT NULL DEFAULT ''",
        "path": "TEXT NOT NULL DEFAULT 'tien'",
        "realm_index": "INTEGER NOT NULL DEFAULT 0",
        "realm_layer": "INTEGER NOT NULL DEFAULT 1",
        "cultivation": "INTEGER NOT NULL DEFAULT 0",
        "spirit_stones": "INTEGER NOT NULL DEFAULT 1000",
        "root": "INTEGER NOT NULL DEFAULT 50",
        "insight": "INTEGER NOT NULL DEFAULT 50",
        "luck": "INTEGER NOT NULL DEFAULT 50",
        "fate": "INTEGER NOT NULL DEFAULT 50",
        "mind": "INTEGER NOT NULL DEFAULT 50",
        "destiny": "TEXT NOT NULL DEFAULT ''",
        "talent": "TEXT NOT NULL DEFAULT ''",
        "hp": "INTEGER NOT NULL DEFAULT 100",
        "max_hp": "INTEGER NOT NULL DEFAULT 100",
        "attack": "INTEGER NOT NULL DEFAULT 10",
        "defense": "INTEGER NOT NULL DEFAULT 5",
        "injury": "INTEGER NOT NULL DEFAULT 0",
        "lifespan": "INTEGER NOT NULL DEFAULT 100",
        "dao_type": "TEXT NOT NULL DEFAULT ''",
        "dao_stage": "INTEGER NOT NULL DEFAULT 0",
        "dao_insight": "INTEGER NOT NULL DEFAULT 0",
        "sect_id": "TEXT",
        "explore_zone": "TEXT NOT NULL DEFAULT 'hoangnguyen'",
        "loadout": "TEXT NOT NULL DEFAULT '{}'",
        "equipped": "TEXT NOT NULL DEFAULT ''",
        "last_cultivate": "INTEGER NOT NULL DEFAULT 0",
        "last_explore": "INTEGER NOT NULL DEFAULT 0",
        "last_hunt": "INTEGER NOT NULL DEFAULT 0",
        "last_daily": "INTEGER NOT NULL DEFAULT 0",
        "daily_streak": "INTEGER NOT NULL DEFAULT 0",
        "be_quan_active": "INTEGER NOT NULL DEFAULT 0",
        "be_quan_last_tick": "INTEGER NOT NULL DEFAULT 0",
        "be_quan_prepaid": "INTEGER NOT NULL DEFAULT 0",
        "trial_floor": "INTEGER NOT NULL DEFAULT 0",
        "trial_attempts": "INTEGER NOT NULL DEFAULT 0",
        "trial_day": "TEXT NOT NULL DEFAULT ''",
        "ascension_floor": "INTEGER NOT NULL DEFAULT 0",
        "created_at": "INTEGER NOT NULL DEFAULT 0",
    },
    "sects": {
        "tower_floor": "INTEGER NOT NULL DEFAULT 0",
        "mission_day": "TEXT NOT NULL DEFAULT ''",
        "mission_key": "TEXT NOT NULL DEFAULT ''",
        "mission_progress": "INTEGER NOT NULL DEFAULT 0",
    },
}


def _table_columns(db, table: str) -> set[str]:
    return {row["name"] for row in db.fetchall(f"PRAGMA table_info({table})")}


def ensure_schema(db) -> None:
    """Create missing tables and repair known missing columns."""
    for stmt in DDL.strip().split(";"):
        statement = stmt.strip()
        if statement:
            db.execute(statement)

    for table, columns in _REQUIRED_COLUMNS.items():
        existing = _table_columns(db, table)
        for name, definition in columns.items():
            if name not in existing:
                db.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

    if db.fetchone("SELECT value FROM schema_meta WHERE key='version'") is None:
        db.execute("INSERT INTO schema_meta(key, value) VALUES('version', '0')")
