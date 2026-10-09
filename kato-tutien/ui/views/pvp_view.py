from __future__ import annotations

import discord

from game.content.items import ITEMS
from game.services.errors import GameError
from game.utils import fmt_amount
from ui.embeds import base_embed, error_embed
from ui.emoji import EMOJI


RARITY_ICONS = {"Phàm": "⚪", "Hoàng": "🟢", "Huyền": "🔵", "Địa": "🟣", "Thiên": "🟠", "Tiên": "🔴"}


def _stake_text(stake: dict) -> str:
    if stake["type"] == "stones":
        return f"{fmt_amount(stake['amount'])} {EMOJI['spirit_stone']} linh thạch"
    item = ITEMS.get(stake["item_id"], {})
    return f"{item.get('name', stake['item_id'])} ×{stake['amount']}"


def challenge_embed(challenge: dict) -> discord.Embed:
    ratio = challenge["challenger_share"]
    share_text = "50% / 50%" if ratio == 50 else (f"45% / 55%" if ratio == 45 else "55% / 45%")
    stake_a = _stake_text(challenge["stake"])
    stake_b = _stake_text({**challenge["stake"], "amount": challenge["target_amount"]})
    embed = base_embed("⚔️ Lời Khiêu Chiến PvP", f"<@{challenge['challenger_id']}> thách đấu <@{challenge['target_id']}>!\n\n**Cược của người thách đấu:** {stake_a}\n**Cược cần có:** {stake_b}\n**Tỷ lệ góp cược:** {share_text}\n\nNgười được thách đấu có 3 phút để nhận lời. Vật cược chỉ bị trừ khi nhận lời.")
    embed.set_footer(text=f"Mã trận: {challenge['id']} · Không nhận lời thì không mất gì")
    return embed


def match_embed(match: dict) -> discord.Embed:
    challenger_id, target_id = match["challenger_id"], match["target_id"]
    hp_a, hp_b = match["hp"][challenger_id], match["hp"][target_id]
    max_a, max_b = match["max_hp"][challenger_id], match["max_hp"][target_id]
    if match["status"] == "finished":
        winner_id = match.get("winner_id")
        winner_name = match["challenger_name"] if winner_id == challenger_id else match["target_name"]
        desc = f"🏆 **{winner_name}** chiến thắng!\nVật cược đã được trao cho người thắng."
    elif match["status"] == "refunded":
        desc = "🤝 Trận đấu đã dừng; vật cược được hoàn lại cho hai bên."
    else:
        turn_name = match["challenger_name"] if match["turn"] == challenger_id else match["target_name"]
        desc = f"**Đến lượt:** <@{match['turn']}> ({turn_name})\n\n**{match['challenger_name']}**\n{EMOJI['hp']} HP: **{hp_a}/{max_a}**\n\n**{match['target_name']}**\n{EMOJI['hp']} HP: **{hp_b}/{max_b}**"
    e = base_embed("⚔️ Đấu Trường PvP", desc)
    e.add_field(name="Vật cược", value=f"Bên A: {_stake_text(match['stake_a'])}\nBên B: {_stake_text(match['stake_b'])}", inline=False)
    if match.get("log"):
        e.add_field(name="Diễn biến", value="\n".join(match["log"][-6:])[:1024], inline=False)
    return e


class PvpChallengeView(discord.ui.View):
    def __init__(self, engine, challenge: dict, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.challenge = challenge
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) != self.challenge["target_id"]:
            await interaction.response.send_message("Chỉ người được thách đấu mới có thể nhận lời hoặc từ chối.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Nhận lời", emoji=EMOJI["ok"], style=discord.ButtonStyle.success)
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            match = self.engine.pvp.accept(self.challenge["id"], str(interaction.user.id))
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)
            return
        view = PvpMatchView(self.engine, match)
        await interaction.response.edit_message(embed=match_embed(match), view=view)
        view.message = interaction.message
        self.stop()

    @discord.ui.button(label="Từ chối", emoji=EMOJI["no"], style=discord.ButtonStyle.danger)
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.engine.pvp.challenges.pop(self.challenge["id"], None)
        await interaction.response.edit_message(embed=base_embed("❌ Đã từ chối khiêu chiến", "Không bên nào bị trừ vật cược."), view=None)
        self.stop()

    async def on_timeout(self):
        self.engine.pvp.challenges.pop(self.challenge["id"], None)
        if self.message:
            try:
                await self.message.edit(embed=base_embed("⌛ Hết hạn khiêu chiến", "Lời khiêu chiến đã hết hạn; không bên nào mất vật cược."), view=None)
            except (discord.HTTPException, discord.NotFound):
                pass


class PvpMatchView(discord.ui.View):
    def __init__(self, engine, match: dict, timeout: float = 900):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.match = match
        self.message = None

    async def _act(self, interaction: discord.Interaction, action: str):
        try:
            match = self.engine.pvp.act(self.match["id"], str(interaction.user.id), action)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)
            return
        self.match = match
        if match["status"] != "active":
            for child in self.children:
                child.disabled = True
            self.stop()
        await interaction.response.edit_message(embed=match_embed(match), view=self if match["status"] == "active" else None)

    @discord.ui.button(label="Tấn công", emoji=EMOJI["attack"], style=discord.ButtonStyle.danger, row=0)
    async def attack_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._act(interaction, "attack")

    @discord.ui.button(label="Hộ thể", emoji="🛡️", style=discord.ButtonStyle.primary, row=0)
    async def guard_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._act(interaction, "guard")

    async def on_timeout(self):
        match = self.engine.pvp.cancel(self.match["id"])
        if self.message and match:
            try:
                await self.message.edit(embed=match_embed(match), view=None)
            except (discord.HTTPException, discord.NotFound):
                pass
