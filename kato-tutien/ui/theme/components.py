"""Shared constructors for tidy, mobile-friendly Discord RPG controls."""
from __future__ import annotations

from typing import Any, Callable
import discord

from ui.theme.tokens import BUTTON_ROLES

_STYLE_MAP = {
    "primary": discord.ButtonStyle.primary,
    "secondary": discord.ButtonStyle.secondary,
    "success": discord.ButtonStyle.success,
    "danger": discord.ButtonStyle.danger,
    "link": discord.ButtonStyle.link,
}


def themed_button(
    label: str,
    *,
    role: str = "navigation",
    emoji: Any = None,
    row: int | None = None,
    disabled: bool = False,
    custom_id: str | None = None,
    callback: Callable[..., Any] | None = None,
) -> discord.ui.Button:
    """Build a button with predictable sizing and semantic role colors."""
    mapped = BUTTON_ROLES.get(role, "secondary")
    kwargs: dict[str, Any] = {
        "label": (label or "Hành động")[:80],
        "style": _STYLE_MAP[mapped],
        "disabled": disabled,
    }
    if emoji is not None:
        kwargs["emoji"] = emoji
    if row is not None:
        kwargs["row"] = max(0, min(4, int(row)))
    if custom_id is not None:
        kwargs["custom_id"] = custom_id[:100]
    button = discord.ui.Button(**kwargs)
    if callback is not None:
        button.callback = callback
    return button


def themed_select(
    *,
    placeholder: str,
    options: list[discord.SelectOption],
    row: int = 0,
    min_values: int = 1,
    max_values: int = 1,
    disabled: bool = False,
) -> discord.ui.Select:
    """Create a select menu within Discord's option and selection limits."""
    safe_options = list(options[:25])
    if not safe_options:
        safe_options = [discord.SelectOption(label="Chưa có lựa chọn", value="__empty__", description="Hiện chưa có dữ liệu.")]
        disabled = True
    min_allowed = max(0, min(int(min_values), len(safe_options)))
    max_allowed = max(1, min(int(max_values), len(safe_options), 25))
    if min_allowed > max_allowed:
        min_allowed = max_allowed
    return discord.ui.Select(
        placeholder=(placeholder or "Chọn một mục…")[:150],
        options=safe_options,
        row=max(0, min(4, int(row))),
        min_values=min_allowed,
        max_values=max_allowed,
        disabled=disabled,
    )
