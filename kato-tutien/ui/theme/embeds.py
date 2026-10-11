"""Branded embed factory and reusable, compact RPG-panel helpers."""
from __future__ import annotations

import discord

from ui.theme.tokens import BRAND_FOOTER, BRAND_NAME, COLOR_MAIN, color_for_title


def create_embed(
    title: str,
    description: str = "",
    color: int | None = None,
    *,
    footer: str = BRAND_FOOTER,
    author: str = BRAND_NAME,
) -> discord.Embed:
    """Create the shared Kato RPG panel without constraining feature content."""
    embed = discord.Embed(
        title=(title or "Kato Tu Tiên")[:256],
        description=description or None,
        color=color if color is not None else color_for_title(title),
    )
    if author:
        embed.set_author(name=author[:256])
    if footer:
        embed.set_footer(text=footer[:2048])
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
    embed.add_field(name=(title or "Thông tin")[:256], value=safe_value[:1024], inline=inline)
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
