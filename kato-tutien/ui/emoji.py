from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

# Custom Discord emoji are enabled by default. Set KATO_CUSTOM_EMOJI=0 to
# use the Unicode fallback throughout the UI.
_TRUE_VALUES = {"1", "true", "yes", "on"}
_CUSTOM_ENABLED = os.getenv("KATO_CUSTOM_EMOJI", "1").strip().lower() in _TRUE_VALUES
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
    "heavenly_tribulation": _icon("heavenly_tribulation", "🌩️"),
    "recover": _icon("recover", "💚"),
    "level_up": _icon("level_up", "✨"),
    "victory": _icon("victory", "🏆"),
    "defeat": _icon("defeat", "💀"),
    "reward": _icon("reward", "🎁"),

    # Frequently referenced GUI keys. When no dedicated custom icon exists,
    # these keep the proper Unicode glyph rather than silently using a wrong icon.
    "home": _icon("home", "🏠"),
    "secret_realm": _icon("secret_realm", "🌌"),
    "dao_lu": _icon("dao_lu", "💞"),
    "admin": _icon("admin", "🔐"),
    "rarity_common": _icon("rarity_common", "⚪"),
    "rarity_uncommon": _icon("rarity_uncommon", "🟢"),
    "rarity_rare": _icon("rarity_rare", "🔵"),
    "rarity_epic": _icon("rarity_epic", "🟣"),
    "rarity_legendary": _icon("rarity_legendary", "🟠"),
    "rarity_mythic": _icon("rarity_mythic", "🔴"),
}

# Map familiar Unicode glyphs used by older screens/content to the semantic
# registry. It lets legacy embed text, combat logs and item descriptions benefit
# from the server emoji tree without rewriting game data or changing game rules.
_UNICODE_SEMANTICS = {
    "💎": "spirit_stone", "🪙": "spirit_stone",
    "🧘": "cultivator", "👹": "demon",
    "❤️": "hp", "❤": "hp", "🗡️": "att", "🗡": "att",
    "🛡️": "def", "🛡": "def", "⚔️": "attack", "⚔": "attack",
    "🌀": "skill", "🎒": "item", "🏃": "flee",
    "📜": "technique", "📖": "technique", "💊": "pill", "🧪": "pill",
    "🔮": "talisman", "✅": "accept", "☑️": "accept", "❌": "reject",
    "🌱": "cultivate", "🌩️": "heavenly_tribulation", "⚡️": "heavenly_tribulation", "⚡": "heavenly_tribulation",
    "💚": "recover", "🩹": "recover", "✨": "level_up",
    "🏆": "victory", "💀": "defeat", "📦": "item",
}


def resolve_emoji(value: Any) -> Any:
    """Replace a recognized Unicode glyph/PartialEmoji with its registry token.

    Other values (including unknown Unicode glyphs and existing custom emoji)
    are returned untouched, which keeps backward compatibility and fallback UI.
    """
    if value is None:
        return None
    if not isinstance(value, str):
        # discord.PartialEmoji exposes .name; don't stringify unknown objects
        # because that can change the type expected by component constructors.
        name = getattr(value, "name", None)
        if isinstance(name, str) and name in _UNICODE_SEMANTICS:
            return EMOJI[_UNICODE_SEMANTICS[name]]
        return value
    if value.startswith("<:") or value.startswith("<a:"):
        return value
    key = _UNICODE_SEMANTICS.get(value)
    return EMOJI[key] if key else value


def extract_leading_emoji(text: Any) -> tuple[Any, str] | None:
    """Return a registered leading glyph as a component icon plus remaining label."""
    if not isinstance(text, str) or not text:
        return None
    for glyph in sorted(_UNICODE_SEMANTICS, key=len, reverse=True):
        if text.startswith(glyph):
            rest = text[len(glyph):]
            if not rest or rest[0].isspace():
                return resolve_emoji(glyph), rest.lstrip()
    return None


def render_emojis(text: Any) -> Any:
    """Replace registered Unicode emoji in visible text with custom server emoji.

    This is presentation-only: values without a matching server emoji are left
    as-is, and gameplay/content data is never mutated.
    """
    if not isinstance(text, str) or not text:
        return text
    # Longer sequences first so variation-selector emoji are not partially matched.
    for glyph in sorted(_UNICODE_SEMANTICS, key=len, reverse=True):
        key = _UNICODE_SEMANTICS[glyph]
        token = EMOJI.get(key, glyph)
        if token != glyph:
            text = text.replace(glyph, token)
    return text
