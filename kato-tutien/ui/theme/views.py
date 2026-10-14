"""Shared visual behavior for all Discord game views.

This module is intentionally presentation-only. Callbacks, permissions and game rules
remain owned by each feature view.
"""
from __future__ import annotations

import unicodedata
from typing import Any

import discord

from ui.theme.tokens import BUTTON_EMOJIS, BUTTON_LABELS, DEFAULT_TIMEOUT
from ui.emoji import resolve_emoji, extract_leading_emoji


def _fold_label(value: str) -> str:
    value = unicodedata.normalize("NFKD", (value or "").casefold())
    folded = "".join(ch for ch in value if not unicodedata.combining(ch)).strip()
    return folded.replace("đ", "d")


def _semantic_role(label: str) -> str | None:
    folded = _fold_label(label)
    # Check success before danger so "Đồng ý" is not treated as "Đóng".
    for role in ("success", "danger", "primary", "navigation"):
        if any(token in folded for token in BUTTON_LABELS[role]):
            return role
    return None


def _semantic_style(label: str) -> discord.ButtonStyle | None:
    role = _semantic_role(label)
    return {
        "danger": discord.ButtonStyle.danger,
        "success": discord.ButtonStyle.success,
        "primary": discord.ButtonStyle.primary,
        "navigation": discord.ButtonStyle.secondary,
    }.get(role)


def _semantic_emoji(label: str) -> str | None:
    folded = _fold_label(label)
    for tokens, emoji in BUTTON_EMOJIS:
        if any(token in folded for token in tokens):
            return emoji
    return None


class ThemedView(discord.ui.View):
    """Apply shared game styling to static and dynamically-created buttons."""

    def __init__(self, *args: Any, **kwargs: Any):
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        super().__init__(*args, **kwargs)
        self.apply_theme()

    def add_item(self, item):
        super().add_item(item)
        self._theme_item(item)
        return self

    def apply_theme(self) -> None:
        for item in self.children:
            self._theme_item(item)

    @staticmethod
    def _theme_item(item) -> None:
        # All normal game views inherit ThemedView, so both explicit Unicode and
        # semantic-label icons are resolved through the shared emoji registry.
        if isinstance(item, discord.ui.Button):
            if item.style != discord.ButtonStyle.link:
                label = item.label or ""
                style = _semantic_style(label)
                if style is not None:
                    item.style = style
                if item.emoji is None:
                    emoji = _semantic_emoji(label)
                    if emoji:
                        item.emoji = emoji
                    else:
                        leading = extract_leading_emoji(label)
                        if leading:
                            item.emoji, item.label = leading[0], leading[1][:80]
            if item.emoji is not None:
                item.emoji = resolve_emoji(item.emoji)
            return

        # Discord select options are separate objects; translate their icons too.
        options = getattr(item, "options", None)
        if options:
            for option in options:
                if getattr(option, "emoji", None) is not None:
                    option.emoji = resolve_emoji(option.emoji)
                else:
                    leading = extract_leading_emoji(getattr(option, "label", ""))
                    if leading:
                        option.emoji, option.label = leading[0], leading[1][:100]
