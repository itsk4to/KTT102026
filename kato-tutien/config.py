"""Central configuration — env only, no secrets in code."""
from __future__ import annotations

import os


def env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


TOKEN = env("DISCORD_TOKEN")
DB_PATH = env("KATO_DB_PATH", "kato_tutien.db")
OWNER_IDS = {x.strip() for x in env("KATO_OWNER_IDS").split(",") if x.strip()}
ADMIN_PASSWORD = env("KATO_ADMIN_PASSWORD")
MOD_ADMIN_ROLE_IDS = {
    int(value.strip()) for value in env("KATO_MOD_ADMIN_ROLE_IDS").split(",")
    if value.strip().isdigit() and int(value.strip()) > 0
}
MODERATOR_ROLE_IDS = {
    int(value.strip()) for value in env("KATO_MODERATOR_ROLE_IDS").split(",")
    if value.strip().isdigit() and int(value.strip()) > 0
}
try:
    MOD_LOG_CHANNEL_ID = int(env("KATO_MOD_LOG_CHANNEL_ID", "0") or "0")
except ValueError:
    MOD_LOG_CHANNEL_ID = 0

def _positive_int_env(name: str, default: int = 0) -> int:
    try:
        value = int(env(name, str(default)) or str(default))
        return value if value > 0 else default
    except ValueError:
        return default

PRISON_ROLE_ID = _positive_int_env("KATO_PRISON_ROLE_ID")
PRISON_CHANNEL_ID = _positive_int_env("KATO_PRISON_CHANNEL_ID")
PRISON_ANNOUNCE_CHANNEL_ID = _positive_int_env("KATO_PRISON_ANNOUNCE_CHANNEL_ID")
PRISON_COOLDOWN_SECONDS = _positive_int_env("KATO_PRISON_COOLDOWN_SECONDS", 30)
PRISON_MAX_REQUIRED_STONES = _positive_int_env("KATO_PRISON_MAX_REQUIRED_STONES", 1000000)
CUSTOM_EMOJI = env("KATO_CUSTOM_EMOJI", "1").lower() in {"1", "true", "yes", "on"}

# Gameplay constants
CULTIVATE_COOLDOWN = 25
EXPLORE_COOLDOWN = 90
HUNT_COOLDOWN = 75
SONG_TU_COOLDOWN = 30 * 60
DAILY_COOLDOWN = 24 * 60 * 60
STARTING_STONES = 1000
MARKET_TAX_RATE = 0.02  # seller receives 98%
BE_QUAN_COST = 50
BE_QUAN_INTERVAL = 5 * 60
ADMIN_SESSION_TTL = 24 * 60 * 60  # One-day admin session
GACHA_TICKET_ID = "thien_co_lenh"
