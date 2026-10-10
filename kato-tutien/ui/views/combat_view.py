from __future__ import annotations

import logging

import discord

from ui.theme.views import ThemedView
from game.content.items import ITEMS
from game.services.errors import GameError
from ui.emoji import EMOJI
from ui.embeds import combat_embed, error_embed


logger = logging.getLogger(__name__)


def build_combat_embed(engine, user_id: str, encounter) -> discord.Embed:
    player = engine.players.get(str(user_id))
    stats = engine.combat.battle_stats(player) if player else None
    return combat_embed(encounter, player, combat_stats=stats)


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
        super().__init__(placeholder="Chọn công pháp để thi triển…", options=options, row=0, disabled=not skills)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "__empty__":
            await interaction.response.send_message(
                "Ngươi chưa học công pháp nào dùng được trong chiến đấu. Hãy mua công pháp, sau đó dùng `.hoc <ID>`.",
                ephemeral=True,
            )
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
            options = [discord.SelectOption(label="Không có vật phẩm hồi phục", value="__empty__", emoji=EMOJI["no"])]
        super().__init__(placeholder="Chọn vật phẩm hồi phục…", options=options, row=1, disabled=not items)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "__empty__":
            await interaction.response.send_message("Không có vật phẩm dùng được trong trận.", ephemeral=True)
            return
        await self.owner.perform(interaction, "item", self.values[0])


class CombatView(ThemedView):
    """A fresh view is created after every turn to keep Discord's component IDs in sync.

    Each view also remembers the encounter turn it represents. If an older/duplicate GUI
    is clicked, it only refreshes the message; it cannot execute an extra combat action.
    """

    def __init__(self, engine, user_id: str, timeout: float = 600):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = str(user_id)
        self._busy = False
        encounter = self.engine.combat.get_encounter(self.user_id)
        self._turn_number = encounter.turn_number if encounter else -1
        self.rebuild()

    def _guard(self, interaction: discord.Interaction) -> bool:
        return str(interaction.user.id) == self.user_id

    def _current_embed(self, encounter) -> discord.Embed:
        return build_combat_embed(self.engine, self.user_id, encounter)

    def rebuild(self):
        self.clear_items()
        self.add_item(CombatSkillSelect(self))
        self.add_item(CombatItemSelect(self))

        attack = discord.ui.Button(label="Tấn công", emoji=EMOJI["attack"], style=discord.ButtonStyle.danger, row=2)
        attack.callback = self._attack
        self.add_item(attack)

        skill = discord.ui.Button(label="Kỹ năng", emoji=EMOJI["skill"], style=discord.ButtonStyle.primary, row=2)
        skill.callback = self._skill_hint
        self.add_item(skill)

        item = discord.ui.Button(label="Dùng vật phẩm", emoji=EMOJI["item"], style=discord.ButtonStyle.success, row=2)
        item.callback = self._item_hint
        self.add_item(item)

        flee = discord.ui.Button(label="Bỏ chạy", emoji=EMOJI["flee"], style=discord.ButtonStyle.secondary, row=2)
        flee.callback = self._flee
        self.add_item(flee)

    async def _skill_hint(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Không phải trận của ngươi.", ephemeral=True)
            return
        await interaction.response.send_message("Chọn công pháp ở menu đầu tiên; chọn xong sẽ thi triển ngay.", ephemeral=True)

    async def _item_hint(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Không phải trận của ngươi.", ephemeral=True)
            return
        await interaction.response.send_message("Chọn vật phẩm hồi phục ở menu thứ hai; chọn xong sẽ dùng ngay.", ephemeral=True)

    async def perform(self, interaction: discord.Interaction, action: str, value: str):
        if action == "skill":
            operation = lambda: self.engine.combat.skill(self.user_id, value)
        elif action == "item":
            operation = lambda: self.engine.combat.use_item(self.user_id, value)
        else:
            await interaction.response.send_message("Thao tác chiến đấu không hợp lệ.", ephemeral=True)
            return
        await self._execute(interaction, operation)

    async def _execute(self, interaction: discord.Interaction, operation):
        if not self._guard(interaction):
            await interaction.response.send_message("Không phải trận của ngươi.", ephemeral=True)
            return
        if self._busy:
            await interaction.response.send_message("Lượt chiến đấu đang được xử lý, chờ một chút nhé.", ephemeral=True)
            return

        current = self.engine.combat.get_encounter(self.user_id)
        if not current or current.finished:
            self._busy = True
            await interaction.response.edit_message(
                embed=error_embed("Trận đấu đã kết thúc. Hãy mở `.khampha` để tiếp tục hành trình."),
                view=None,
            )
            return
        if current.turn_number != self._turn_number:
            # The player has another open battle GUI. Refresh this one without consuming a turn.
            self._busy = True
            fresh_view = CombatView(self.engine, self.user_id, timeout=self.timeout or 600)
            await interaction.response.edit_message(
                embed=self._current_embed(current),
                view=fresh_view,
            )
            return

        self._busy = True
        try:
            result = operation()
        except GameError as exc:
            # A validation error did not advance combat; keep this view usable.
            self._busy = False
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)
            return
        except Exception:
            logger.exception("Unhandled combat action error (user_id=%s)", self.user_id)
            current = self.engine.combat.get_encounter(self.user_id)
            if current and not current.finished:
                fresh_view = CombatView(self.engine, self.user_id, timeout=self.timeout or 600)
                embed = self._current_embed(current)
                embed.add_field(
                    name="Đã đồng bộ trận đấu",
                    value="Có lỗi trong lượt vừa rồi. Trạng thái đã được tải lại; hãy kiểm tra diễn biến trước khi chọn tiếp.",
                    inline=False,
                )
                await interaction.response.edit_message(embed=embed, view=fresh_view)
            else:
                await interaction.response.send_message(
                    "Trận đấu gặp lỗi ngoài dự kiến và đã kết thúc hoặc không còn khả dụng. Hãy mở `.khampha` lại; lỗi đã được ghi log.",
                    ephemeral=True,
                )
            return

        encounter = result["encounter"]
        finished = bool(result.get("finished") or result.get("fled") or encounter.finished)
        next_view = None if finished else CombatView(self.engine, self.user_id, timeout=self.timeout or 600)
        await interaction.response.edit_message(embed=self._current_embed(encounter), view=next_view)

    async def _attack(self, interaction: discord.Interaction):
        await self._execute(interaction, lambda: self.engine.combat.attack(self.user_id))

    async def _flee(self, interaction: discord.Interaction):
        await self._execute(interaction, lambda: self.engine.combat.flee(self.user_id))
