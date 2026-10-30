"""Shared visual behavior for all Discord game views.

This module is intentionally presentation-only. Callbacks, permissions and game rules
remain owned by each feature view.
"""
from __future__ import annotations

import unicodedata
from typing import Any

import discord
import config

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


async def prison_view_interaction_allowed(view: Any, interaction: discord.Interaction) -> bool:
    """Prevent already-posted game panels from bypassing an active prison sentence."""
    engine = getattr(view, "engine", None)
    guild = interaction.guild
    if engine is None:
        return True
    try:
        session = engine.prison.get_active_session_for_user(str(interaction.user.id))
    except Exception:
        import logging
        logging.getLogger("kato.prison").exception("Could not verify prison state for component interaction")
        await interaction.response.send_message(
            "Không thể xác minh trạng thái lao tù lúc này. Thao tác bị chặn an toàn; hãy thử lại sau.",
            ephemeral=True,
        )
        return False
    jail_context = bool(
        session and guild is not None
        and str(guild.id) == str(session["guild_id"])
        and interaction.channel_id == config.PRISON_CHANNEL_ID
    )
    if session and view.__class__.__name__ == "PathChoiceView":
        if not jail_context:
            await interaction.response.send_message(
                "Đang chịu phạt tù: chỉ có thể đăng ký `.tutien` trong kênh lao ngục.",
                ephemeral=True,
            )
            return False
        try:
            already_registered = engine.players.exists(str(interaction.user.id))
        except Exception:
            import logging
            logging.getLogger("kato.prison").exception("Could not verify prisoner registration state")
            await interaction.response.send_message(
                "Không thể xác minh nhân vật lúc này. Thao tác đăng ký bị chặn an toàn; hãy thử lại sau.",
                ephemeral=True,
            )
            return False
        if already_registered:
            await interaction.response.send_message(
                "Nhân vật của ngươi đã được đăng ký. Hãy dùng `.kthac` trong kênh lao ngục để tiếp tục lao dịch.",
                ephemeral=True,
            )
            return False
    if session and (not jail_context or view.__class__.__name__ != "PathChoiceView"):
        await interaction.response.send_message(
            "⛓️ Đang chịu phạt tù: chỉ được thao tác đăng ký `.tutien` trong kênh lao ngục. Các bảng gameplay khác tạm khóa.",
            ephemeral=True,
        )
        return False
    return True


class ThemedView(discord.ui.View):
    """Apply shared game styling to static and dynamically-created buttons."""

    def __init__(self, *args: Any, **kwargs: Any):
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        super().__init__(*args, **kwargs)
        self.apply_theme()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await prison_view_interaction_allowed(self, interaction)

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
