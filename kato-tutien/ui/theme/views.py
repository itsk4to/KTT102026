"""Reusable Discord View base with consistent semantic button styling.

This module is presentation-only. It does not own callbacks, permissions or game rules.
All feature views inherit from :class:`ThemedView`; the existing interaction logic stays
in its original module.
"""
from __future__ import annotations

import unicodedata
from typing import Any

import discord

from ui.theme.tokens import BUTTON_LABELS, DEFAULT_TIMEOUT


def _fold_label(value: str) -> str:
    """Normalize Vietnamese labels so rules work with or without accents."""
    value = unicodedata.normalize("NFKD", value.casefold())
    folded = "".join(ch for ch in value if not unicodedata.combining(ch)).strip()
    # Vietnamese D-stroke (đ/Đ) does not decompose under NFKD.
    return folded.replace("đ", "d")


def _semantic_style(label: str) -> discord.ButtonStyle | None:
    folded = _fold_label(label)
    # Confirmation comes first because accent-folding makes "Đồng ý" and "Đóng"
    # share the substring "dong"; the full confirmation token must win.
    for role in ("success", "danger", "primary", "navigation"):
        if any(token in folded for token in BUTTON_LABELS[role]):
            return {
                "danger": discord.ButtonStyle.danger,
                "success": discord.ButtonStyle.success,
                "primary": discord.ButtonStyle.primary,
                "navigation": discord.ButtonStyle.secondary,
            }[role]
    return None


class ThemedView(discord.ui.View):
    """Shared view base that normalizes action colors across every GUI.

    A view's callbacks and state remain in its own feature module. Buttons created by
    decorators and buttons added dynamically both pass through the same style policy.
    """

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
