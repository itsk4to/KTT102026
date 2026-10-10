"""Central configuration — env only, no secrets in code."""
from __future__ import annotations

import os


def env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


TOKEN = env("DISCORD_TOKEN")
DB_PATH = env("KATO_DB_PATH", "kato_tutien.db")
OWNER_IDS = {x.strip() for x in env("KATO_OWNER_IDS").split(",") if x.strip()}
ADMIN_PASSWORD = env("KATO_ADMIN_PASSWORD")
CUSTOM_EMOJI = env("KATO_CUSTOM_EMOJI", "0").lower() in {"1", "true", "yes", "on"}

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
