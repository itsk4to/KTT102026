from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

# Custom Discord emoji are deliberately disabled by default. Normal Unicode emoji
# are rendered everywhere unless the owner explicitly enables the server map.
_TRUE_VALUES = {"1", "true", "yes", "on"}
_CUSTOM_ENABLED = os.getenv("KATO_CUSTOM_EMOJI", "0").strip().lower() in _TRUE_VALUES
_CUSTOM_EMOJI_RE = re.compile(r"<a?:[A-Za-z0-9_~]+:[0-9]{15,}>\Z")
_CUSTOM_EMOJI_FILE = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "emojis"
    / "server"
    / "emojis.json"
)


def _load_custom_emojis() -> dict[str, str]:
    """Load opt-in server emojis from the dedicated asset tree.

    Only valid Discord custom-emoji tokens are accepted. If the file is missing,
    malformed, or custom emoji are disabled, the Unicode defaults remain active.
    """
    if not _CUSTOM_ENABLED:
        return {}
    try:
        payload: Any = json.loads(_CUSTOM_EMOJI_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    entries = payload.get("emojis", payload)
    if not isinstance(entries, dict):
        return {}
    return {
        str(key): value
        for key, value in entries.items()
        if isinstance(value, str) and _CUSTOM_EMOJI_RE.fullmatch(value)
    }


_SERVER_EMOJI = _load_custom_emojis()


def _icon(key: str, fallback: str) -> str:
    return _SERVER_EMOJI.get(key, fallback)


# Centralized player-facing emoji registry. UI code should use these semantic keys
# rather than embedding Discord custom-emoji syntax in Python source.
EMOJI = {
    # Core gameplay
    "spirit_stone": _icon("spirit_stone", "💎"),
    "ok": _icon("ok", "✅"),
    "no": _icon("no", "❌"),
    "attack": _icon("attack", "⚔️"),
    "skill": _icon("skill", "🌀"),
    "item": _icon("item", "🎒"),
    "flee": _icon("flee", "🏃"),
    "hp": _icon("hp", "❤️"),
    "def": _icon("def", "🛡️"),
    "att": _icon("att", "🗡️"),
    "technique": _icon("technique", "📜"),
    "pill": _icon("pill", "💊"),
    "talisman": _icon("talisman", "🔮"),
    "cultivator": _icon("cultivator", "🧘"),
    "demon": _icon("demon", "👹"),
    "faction_tien": _icon("faction_tien", "🧘"),
    "faction_ma": _icon("faction_ma", "👹"),

    # Semantic aliases for UI code
    "accept": _icon("accept", "✅"),
    "reject": _icon("reject", "❌"),
    "cultivation": _icon("cultivation", "🧘"),
    "demon_path": _icon("demon_path", "👹"),

    # Navigation / GUI actions
    "all": _icon("all", "📦"),
    "filter": _icon("filter", "🗂️"),
    "use": _icon("use", "🎒"),
    "quantity": _icon("quantity", "🔢"),
    "equip": _icon("equip", "🛡️"),
    "learn": _icon("learn", "📖"),
    "refresh": _icon("refresh", "🔄"),
    "back": _icon("back", "↩️"),
    "close": _icon("close", "✖️"),
    "previous": _icon("previous", "◀️"),
    "next": _icon("next", "▶️"),

    # Inventory/category icons
    "consumable": _icon("consumable", "💊"),
    "equipment": _icon("equipment", "🛡️"),
    "weapon": _icon("weapon", "⚔️"),
    "artifact": _icon("artifact", "💠"),
    "armor": _icon("armor", "🛡️"),
    "accessory": _icon("accessory", "💍"),
    "combat_item": _icon("combat_item", "⚔️"),
    "unknown": _icon("unknown", "📦"),

    # Main sections
    "sect": _icon("sect", "🏯"),
    "dao": _icon("dao", "☯️"),
    "cultivate": _icon("cultivate", "🧘"),
    "explore": _icon("explore", "🗺️"),
    "shop": _icon("shop", "🛍️"),
    "breakthrough": _icon("breakthrough", "✨"),
}
