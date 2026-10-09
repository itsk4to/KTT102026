"""Shared component constructors for consistent labels and native Discord styles."""
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
    """Build a Discord button through the common visual vocabulary."""
    mapped = BUTTON_ROLES.get(role, "secondary")
    kwargs: dict[str, Any] = {
        "label": label,
        "style": _STYLE_MAP[mapped],
        "disabled": disabled,
    }
    if emoji is not None:
        kwargs["emoji"] = emoji
    if row is not None:
        kwargs["row"] = row
    if custom_id is not None:
        kwargs["custom_id"] = custom_id
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
    """Build a single-purpose select menu with bounded, predictable defaults."""
    return discord.ui.Select(
        placeholder=placeholder[:150],
        options=options[:25],
        row=row,
        min_values=min_values,
        max_values=max_values,
        disabled=disabled,
    )
