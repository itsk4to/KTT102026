from __future__ import annotations

import discord

from ui.emoji import EMOJI
from ui.theme.views import ThemedView
from ui.theme.components import themed_button
from ui.views.main_menu_view import MainMenuView, build_main_embed


class HelpView(ThemedView):
    """Cẩm nang người mới — phân trang, dễ bấm trên mobile."""

    def __init__(self, pages: list[discord.Embed], engine, user_id: str, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.engine = engine
        self.user_id = user_id
        self.page_index = 0
        self._sync_buttons()

    def _sync_buttons(self) -> None:
        """
        Row 0 — lật trang (gần nội dung)
        Row 1 — Trung tâm · Khép lại (thumb zone)
        """
        self.clear_items()
        total = max(1, len(self.pages))

        previous = themed_button(
            "Trước",
            role="navigation",
            emoji=EMOJI.get("previous", "◀️"),
            row=0,
            disabled=self.page_index <= 0,
            callback=self._previous,
        )
        next_page = themed_button(
            "Sau",
            role="primary",
            emoji=EMOJI.get("next", "▶️"),
            row=0,
            disabled=self.page_index >= total - 1,
            callback=self._next,
        )
        self.add_item(previous)
        self.add_item(next_page)

        home = themed_button(
            "Trung tâm",
            role="navigation",
            emoji=EMOJI.get("home", "🏠"),
            row=1,
            callback=self._home,
        )
        close = themed_button(
            "Khép lại",
            role="danger",
            emoji=EMOJI.get("close", "✖️"),
            row=1,
            callback=self._close,
        )
        self.add_item(home)
        self.add_item(close)

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) == self.user_id:
            return True
        await interaction.response.send_message(
            "Cẩm nang này không thuộc về đạo hữu.",
            ephemeral=True,
        )
        return False

    async def _show_page(self, interaction: discord.Interaction, target: int) -> None:
        if not await self._guard(interaction):
            return
        self.page_index = max(0, min(target, len(self.pages) - 1))
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.pages[self.page_index], view=self)

    async def _previous(self, interaction: discord.Interaction) -> None:
        await self._show_page(interaction, self.page_index - 1)

    async def _next(self, interaction: discord.Interaction) -> None:
        await self._show_page(interaction, self.page_index + 1)

    async def _home(self, interaction: discord.Interaction) -> None:
        if not await self._guard(interaction):
            return
        await interaction.response.edit_message(
            embed=build_main_embed(self.engine, self.user_id),
            view=MainMenuView(self.engine, self.user_id),
        )

    async def _close(self, interaction: discord.Interaction) -> None:
        if not await self._guard(interaction):
            return
        self.stop()
        await interaction.response.edit_message(view=None)
