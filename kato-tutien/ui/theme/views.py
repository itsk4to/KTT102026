"""Shared visual behavior for all Discord game views.

This module is intentionally presentation-only. Callbacks, permissions and game rules
remain owned by each feature view.
"""
from __future__ import annotations

import unicodedata
from typing import Any

import discord

from ui.theme.tokens import BUTTON_EMOJIS, BUTTON_LABELS, DEFAULT_TIMEOUT


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
        if not isinstance(item, discord.ui.Button):
            return
        if item.style == discord.ButtonStyle.link:
            return
        label = item.label or ""
        style = _semantic_style(label)
        if style is not None:
            item.style = style
        # Keep explicitly set emoji; supply a consistent glyph only when absent.
        if item.emoji is None:
            emoji = _semantic_emoji(label)
            if emoji:
                item.emoji = emoji
