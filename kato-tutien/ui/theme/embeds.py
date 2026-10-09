"""Shared, branded embed factory and small layout helpers."""
from __future__ import annotations

import discord

from ui.theme.tokens import BRAND_FOOTER, COLOR_MAIN


def create_embed(
    title: str,
    description: str = "",
    color: int = COLOR_MAIN,
    *,
    footer: str = BRAND_FOOTER,
) -> discord.Embed:
    """Create a consistent embed while leaving feature-specific content flexible."""
    embed = discord.Embed(
        title=title,
        description=description or None,
        color=color,
    )
    if footer:
        embed.set_footer(text=footer)
    return embed


def add_section(
    embed: discord.Embed,
    title: str,
    value: str,
    *,
    inline: bool = False,
) -> discord.Embed:
    """Add a field that never renders as empty Discord content."""
    embed.add_field(name=title, value=value.strip() or "Chưa có dữ liệu.", inline=inline)
    return embed
