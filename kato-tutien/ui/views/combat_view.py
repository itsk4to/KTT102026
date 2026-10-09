from __future__ import annotations

import discord

from ui.theme.views import ThemedView
from game.content.items import ITEMS
from game.services.errors import GameError
from ui.emoji import EMOJI
from ui.embeds import combat_embed, error_embed


class CombatSkillSelect(discord.ui.Select):
    def __init__(self, owner: "CombatView"):
        self.owner = owner
        skills = owner.engine.combat.learned_skills(owner.user_id)
        options = [
            discord.SelectOption(
                label=s["name"][:100],
                value=s["id"],
                description=f"{s['stage']} · Cấp {s['mastery']}",
                emoji=EMOJI["skill"],
            ) for s in skills[:25]
        ]
        if not options:
            options = [discord.SelectOption(label="Chưa có kỹ năng", value="__empty__", emoji=EMOJI["no"])]
        super().__init__(placeholder="Chọn kỹ năng…", options=options, row=1, disabled=not skills)

    async def callback(self, interaction: discord.Interaction):
        if not self.owner._guard(interaction):
            await interaction.response.send_message("Không phải trận của ngươi.", ephemeral=True)
            return
        if self.values[0] == "__empty__":
            await interaction.response.send_message("Ngươi chưa học công pháp nào có thể dùng trong chiến đấu.", ephemeral=True)
            return
        await self.owner.perform(interaction, "skill", self.values[0])


class CombatItemSelect(discord.ui.Select):
    def __init__(self, owner: "CombatView"):
        self.owner = owner
        items = []
        for stack in owner.engine.economy.inventory(owner.user_id):
            meta = stack.get("meta", {})
            if meta.get("type") in ("combat_item", "consumable") and meta.get("heal"):
                items.append(stack)
        options = [
            discord.SelectOption(
                label=it["name"][:100],
                value=it["id"],
                description=f"×{it['qty']} · Hồi {it.get('meta', {}).get('heal', 0)} HP",
                emoji=EMOJI["item"],
            ) for it in items[:25]
        ]
        if not options:
            options = [discord.SelectOption(label="Không có vật phẩm chiến đấu", value="__empty__", emoji=EMOJI["no"])]
        super().__init__(placeholder="Chọn vật phẩm…", options=options, row=2, disabled=not items)

    async def callback(self, interaction: discord.Interaction):
        if not self.owner._guard(interaction):
            await interaction.response.send_message("Không phải trận của ngươi.", ephemeral=True)
            return
        if self.values[0] == "__empty__":
            await interaction.response.send_message("Không có vật phẩm dùng được trong trận.", ephemeral=True)
            return
        await self.owner.perform(interaction, "item", self.values[0])


class CombatView(ThemedView):
    def __init__(self, engine, user_id: str, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self.rebuild()

    def _guard(self, interaction: discord.Interaction) -> bool:
        return str(interaction.user.id) == self.user_id

    def rebuild(self):
        self.clear_items()
        self.add_item(CombatSkillSelect(self))
        self.add_item(CombatItemSelect(self))

        attack = discord.ui.Button(label="Tấn công", emoji=EMOJI["attack"], style=discord.ButtonStyle.danger, row=3)
        attack.callback = self._attack
        self.add_item(attack)

        skill = discord.ui.Button(label="Kỹ năng", emoji=EMOJI["skill"], style=discord.ButtonStyle.primary, row=3)
        skill.callback = self._skill_hint
        self.add_item(skill)

        item = discord.ui.Button(label="Dùng vật phẩm", emoji=EMOJI["item"], style=discord.ButtonStyle.success, row=3)
        item.callback = self._item_hint
        self.add_item(item)

        flee = discord.ui.Button(label="Bỏ chạy", emoji=EMOJI["flee"], style=discord.ButtonStyle.secondary, row=3)
        flee.callback = self._flee
        self.add_item(flee)

    async def _skill_hint(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Không phải trận của ngươi.", ephemeral=True)
            return
        await interaction.response.send_message("Chọn kỹ năng ở menu phía trên.", ephemeral=True)

    async def _item_hint(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Không phải trận của ngươi.", ephemeral=True)
            return
        await interaction.response.send_message("Chọn vật phẩm chiến đấu ở menu phía trên.", ephemeral=True)

    async def perform(self, interaction: discord.Interaction, action: str, value: str):
        try:
            if action == "skill":
                result = self.engine.combat.skill(self.user_id, value)
            else:
                result = self.engine.combat.use_item(self.user_id, value)
            enc = result["encounter"]
            await interaction.response.edit_message(
                embed=combat_embed(enc, self.engine.players.get(self.user_id)),
                view=None if result.get("finished") else self,
            )
            if not result.get("finished"):
                self.rebuild()
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _attack(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Không phải trận của ngươi.", ephemeral=True)
            return
        try:
            result = self.engine.combat.attack(self.user_id)
            await interaction.response.edit_message(
                embed=combat_embed(result["encounter"], self.engine.players.get(self.user_id)),
                view=None if result.get("finished") else self,
            )
            if not result.get("finished"):
                self.rebuild()
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _flee(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Không phải trận của ngươi.", ephemeral=True)
            return
        try:
            result = self.engine.combat.flee(self.user_id)
            await interaction.response.edit_message(
                embed=combat_embed(result["encounter"], self.engine.players.get(self.user_id)),
                view=None if result.get("fled") or result.get("finished") else self,
            )
            if not result.get("fled") and not result.get("finished"):
                self.rebuild()
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)
