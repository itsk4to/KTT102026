"""Branded embed factory and reusable, compact RPG-panel helpers."""
from __future__ import annotations

import re

import discord

from ui.theme.tokens import BRAND_FOOTER, BRAND_NAME, COLOR_MAIN, color_for_title
from ui.emoji import render_emojis

_CUSTOM_EMOJI_TOKEN = re.compile(r"<a?:[A-Za-z0-9_~]+:[0-9]{15,}>")


def _limited_text(value: str | None, limit: int) -> str | None:
    """Render custom emoji and trim to Discord's field limit without cutting tokens."""
    if value is None:
        return None
    rendered = render_emojis(value)
    if not isinstance(rendered, str) or len(rendered) <= limit:
        return rendered
    prefix = rendered[:limit]
    # If truncation cuts through a custom emoji token, drop that incomplete token.
    for match in _CUSTOM_EMOJI_TOKEN.finditer(rendered):
        if match.start() < limit < match.end():
            prefix = rendered[:match.start()]
            break
    return prefix


class EmojiAwareEmbed(discord.Embed):
    """Embed that applies the central custom-emoji map to every visible text field."""

    def add_field(self, *, name: str, value: str, inline: bool = True):
        return super().add_field(
            name=_limited_text(name, 256) or "Thông tin",
            value=_limited_text(value, 1024) or "Chưa có dữ liệu.",
            inline=inline,
        )

    def set_field_at(self, index: int, *, name: str, value: str, inline: bool = True):
        return super().set_field_at(
            index, name=_limited_text(name, 256) or "Thông tin",
            value=_limited_text(value, 1024) or "Chưa có dữ liệu.", inline=inline
        )

    def set_author(self, *, name: str, url: str | None = None, icon_url: str | None = None):
        return super().set_author(
            name=_limited_text(name, 256) or "Tu Tiên", url=url, icon_url=icon_url
        )

    def set_footer(self, *, text: str | None = None, icon_url: str | None = None):
        return super().set_footer(text=_limited_text(text, 2048), icon_url=icon_url)


def create_embed(
    title: str,
    description: str = "",
    color: int | None = None,
    *,
    footer: str = BRAND_FOOTER,
    author: str = BRAND_NAME,
) -> discord.Embed:
    """Create the shared Kato RPG panel without constraining feature content."""
    embed = EmojiAwareEmbed(
        title=_limited_text(title or "Kato Tu Tiên", 256) or "Kato Tu Tiên",
        description=_limited_text(description, 4096) or None,
        color=color if color is not None else color_for_title(title),
    )
    if author:
        embed.set_author(name=_limited_text(author, 256) or BRAND_NAME)
    if footer:
        embed.set_footer(text=_limited_text(footer, 2048))
    return embed


def add_section(
    embed: discord.Embed,
    title: str,
    value: str,
    *,
    inline: bool = False,
) -> discord.Embed:
    """Add a non-empty panel section with Discord-safe lengths."""
    safe_value = (value or "Chưa có dữ liệu.").strip() or "Chưa có dữ liệu."
    embed.add_field(name=title or "Thông tin", value=safe_value, inline=inline)
    return embed


def add_stat(embed: discord.Embed, label: str, value: str | int, *, hint: str | None = None, inline: bool = True) -> discord.Embed:
    """Render a compact HUD stat field."""
    text = f"**{value}**"
    if hint:
        text += f"\n{hint}"
    return add_section(embed, label, text, inline=inline)


def add_progress(embed: discord.Embed, label: str, current: int, maximum: int, *, width: int = 12, suffix: str = "") -> discord.Embed:
    maximum = max(1, int(maximum))
    current = max(0, int(current))
    ratio = max(0.0, min(1.0, current / maximum))
    filled = round(ratio * max(4, width))
    bar = "▰" * filled + "▱" * (max(4, width) - filled)
    return add_section(embed, label, f"`{bar}` **{ratio:.0%}**\n{current:,} / {maximum:,}{suffix}", inline=False)
