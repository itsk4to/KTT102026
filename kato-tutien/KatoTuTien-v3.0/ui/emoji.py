from __future__ import annotations

import os

_CUSTOM = os.getenv("KATO_CUSTOM_EMOJI", "1").strip() not in {"0", "false", "False", "no", "off"}


def _icon(custom: str, fallback: str) -> str:
    return custom if _CUSTOM else fallback


EMOJI = {
    "spirit_stone": _icon("<:linhthach:1556648801471701053>", "💎"),
    "attack": _icon("<:tancong:1556657986028568656>", "⚔️"),
    "skill": _icon("<:kinang:1556658019188613150>", "🌀"),
    "item": _icon("<:vatpham:1556658044954214481>", "🎒"),
    "flee": _icon("<:bochay:1556658072850792528>", "🏃"),
    "hp": _icon("<:hp:1556722270918152344>", "❤️"),
    "def": _icon("<:def:1556722328425992242>", "🛡️"),
    "att": _icon("<:att:1556722389973213294>", "🗡️"),
    "technique": _icon("<:congphap:1556722479492243538>", "📜"),
    "pill": _icon("<:danduoc:1556722510962106459>", "💊"),
    "talisman": _icon("<:buachu:1556722564502655076>", "🔮"),
    "ok": _icon("<:dongy:1556653535037366292>", "✅"),
    "no": _icon("<:tuchoi:1556653578649731092>", "❌"),
    "sect": "🏯",
    "dao": "☯️",
    "cultivate": "🧘",
    "explore": "🗺️",
    "shop": "🛍️",
    "breakthrough": "✨",
}
