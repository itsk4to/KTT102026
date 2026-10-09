from __future__ import annotations

import discord

from game.services.errors import GameError
from ui.emoji import EMOJI
from ui.embeds import error_embed, success_embed, cultivation_preview_embed


class BreakthroughItemSelect(discord.ui.Select):
    def __init__(self, owner: "BreakthroughView"):
        self.owner = owner
        inventory = owner.engine.economy.inventory(owner.user_id)
        items = [
            x for x in inventory
            if x.get("meta", {}).get("type") == "consumable"
            and x.get("meta", {}).get("breakthrough_bonus")
        ]
        options = [
            discord.SelectOption(
                label=x["name"][:100], value=x["id"],
                description=f"×{x['qty']} · +{x['meta']['breakthrough_bonus']:.0%} tỷ lệ",
                emoji=EMOJI["pill"],
                default=x["id"] == owner.selected_item,
            ) for x in items[:25]
        ] or [discord.SelectOption(label="Không có đạo cụ hỗ trợ đột phá", value="__empty__", emoji=EMOJI["no"])]
        super().__init__(placeholder="Chọn đan tăng tỷ lệ đột phá…", options=options, row=0, disabled=not items)

    async def callback(self, interaction: discord.Interaction):
        if not self.owner._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        if self.values[0] == "__empty__":
            await interaction.response.send_message("Ngươi chưa có đạo cụ hỗ trợ đột phá.", ephemeral=True)
            return
        try:
            result = self.owner.engine.breakthrough.preview_item(self.owner.user_id, self.values[0])
            self.owner.selected_item = self.values[0]
            self.owner.bonus = result["bonus"]
            self.owner.rebuild()
            await interaction.response.edit_message(embed=self.owner.render_embed(), view=self.owner)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)


class ThunderProtectionSelect(discord.ui.Select):
    def __init__(self, owner: "BreakthroughView"):
        self.owner = owner
        items = owner.engine.breakthrough.thunder_protection_items(owner.user_id)
        options = []
        selected_quantities = {}
        for selection in owner.selected_thunder_items:
            if "::" in selection:
                item_id, quantity_text = selection.rsplit("::", 1)
                selected_quantities[item_id] = quantity_text
            else:
                selected_quantities[selection] = "1"
        for item in items:
            for quantity in range(1, min(3, item["qty"]) + 1):
                effective = owner.engine.breakthrough.stacked_thunder_resistance(item["resistance"], quantity)
                options.append(discord.SelectOption(
                    label=f"{item['name']} ×{quantity}"[:100],
                    value=f"{item['id']}::{quantity}",
                    description=f"Giảm {effective:.0%} sát thương · sở hữu {item['qty']}",
                    emoji=EMOJI.get("pill", "🧪") if item["item"].get("category") == "Đan dược" else "🧿",
                    default=selected_quantities.get(item["id"]) == str(quantity),
                ))
        options = options[:25] or [discord.SelectOption(label="Chưa có vật phẩm hộ kiếp", value="__empty__", emoji="🛡️")]
        max_values = max(1, min(2, len(items)))
        super().__init__(
            placeholder="Chọn đan/bùa giảm sát thương (có thể chọn cả hai)…",
            options=options,
            min_values=0,
            max_values=max_values,
            row=1,
            disabled=not items,
        )

    async def callback(self, interaction: discord.Interaction):
        if not self.owner._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        selections = [x for x in self.values if x != "__empty__"]
        selected_ids = [x.rsplit("::", 1)[0] if "::" in x else x for x in selections]
        if len(selected_ids) != len(set(selected_ids)):
            await interaction.response.send_message(
                "Chọn một mức số lượng cho mỗi loại đan/bùa; có thể phối hợp tối đa hai loại khác nhau.",
                ephemeral=True,
            )
            return
        self.owner.selected_thunder_items = selections
        self.owner.rebuild()
        await interaction.response.edit_message(embed=self.owner.render_embed(), view=self.owner)


class BreakthroughView(discord.ui.View):
    def __init__(self, engine, user_id: str, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self.bonus = 0.0
        self.selected_item: str | None = None
        self.selected_thunder_items: list[str] = []
        self.rebuild()

    def _guard(self, interaction: discord.Interaction) -> bool:
        return str(interaction.user.id) == self.user_id

    def rebuild(self):
        self.clear_items()
        self.add_item(BreakthroughItemSelect(self))
        self.add_item(ThunderProtectionSelect(self))

        accept = discord.ui.Button(label="Đồng ý đột phá", emoji=EMOJI["accept"], style=discord.ButtonStyle.success, row=2)
        accept.callback = self._accept
        self.add_item(accept)
        reject = discord.ui.Button(label="Từ chối", emoji=EMOJI["reject"], style=discord.ButtonStyle.secondary, row=2)
        reject.callback = self._reject
        self.add_item(reject)
        use = discord.ui.Button(label="Dùng đạo cụ", emoji=EMOJI["item"], style=discord.ButtonStyle.primary, row=2)
        use.callback = self._use_hint
        self.add_item(use)

    def render_embed(self) -> discord.Embed:
        preview = self.engine.cultivation.breakthrough_preview(self.user_id, self.bonus)
        embed = cultivation_preview_embed(preview)
        if preview.get("needs_thunder_tribulation"):
            if self.selected_thunder_items:
                protection = []
                selected = {}
                for selection in self.selected_thunder_items:
                    if "::" in selection:
                        selected_id, quantity_text = selection.rsplit("::", 1)
                        selected[selected_id] = int(quantity_text)
                    else:
                        selected[selection] = 1
                for item in self.engine.breakthrough.thunder_protection_items(self.user_id):
                    if item["id"] in selected:
                        quantity = selected[item["id"]]
                        total = self.engine.breakthrough.stacked_thunder_resistance(item["resistance"], quantity)
                        protection.append(f"• **{item['name']} ×{quantity}** · −{total:.0%}")
                value = "\n".join(protection) or "Chưa chọn"
            else:
                value = "Chưa chọn đan/bùa hộ kiếp; ngươi có thể tiếp tục nhưng rủi ro sẽ cao hơn."
            embed.add_field(name="Vật phẩm hộ kiếp", value=value, inline=False)
            embed.set_footer(text="Đan/bùa chỉ bị tiêu hao nếu tỷ lệ đột phá thành công và Cửu Lôi Kiếp bắt đầu.")
        return embed

    async def _accept(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            result = self.engine.breakthrough.breakthrough(
                self.user_id,
                self.bonus,
                self.selected_item,
                thunder_items=self.selected_thunder_items,
            )
            thunder = result.get("thunder_tribulation")
            if thunder and thunder.get("attempted"):
                strike_lines = [
                    f"⚡ **Lôi {hit['strike']}**: −{hit['damage']} HP · còn **{hit['hp_after']} HP**"
                    for hit in thunder.get("strikes", [])
                ]
                detail = "\n".join(strike_lines)
                used = result.get("consumed_thunder_items", [])
                used_text = "\nVật phẩm đã dùng: " + ", ".join(used) if used else "\nVật phẩm hộ kiếp đã dùng: không có"
                summary = (
                    f"**Cửu Lôi Kiếp** · {len(thunder.get('strikes', []))}/9 tia\n"
                    f"Tổng sát thương: **{thunder.get('total_damage', 0)} HP** · "
                    f"Kháng lôi từ vật phẩm: **{thunder.get('resistance', 0.0):.0%}** · "
                    f"Giảm tổng sau phòng ngự: **{thunder.get('total_reduction', 0.0):.0%}**\n\n"
                    f"{detail}{used_text}"
                )
                if result["success"]:
                    await interaction.response.edit_message(
                        embed=success_embed(
                            f"{EMOJI['breakthrough']} Vượt Cửu Lôi Kiếp thành công",
                            f"Ngươi đã chịu đủ chín tia lôi kiếp!\nCảnh giới mới: **{result['realm']}**\n"
                            f"Tỷ lệ đột phá ban đầu: **{result['chance']:.0%}**\n\n{summary}",
                        ),
                        view=None,
                    )
                else:
                    await interaction.response.edit_message(
                        embed=error_embed(
                            f"Ngươi gục trước Cửu Lôi Kiếp; cảnh giới vẫn là **{result['realm']}**.\n"
                            f"Tu vi hao tổn, thương thế tăng và phải hồi phục **{result.get('recovery_seconds', 0)}s**.\n\n{summary}"
                        ),
                        view=None,
                    )
            elif result["success"]:
                await interaction.response.edit_message(
                    embed=success_embed(f"{EMOJI['breakthrough']} Đột phá thành công", f"Cảnh giới: **{result['realm']}** · tỷ lệ **{result['chance']:.0%}**"),
                    view=None,
                )
            else:
                await interaction.response.edit_message(
                    embed=error_embed(
                        f"Đột phá thất bại · tỷ lệ **{result['chance']:.0%}**\n"
                        f"Tu vi bị tổn thất. 🩹 Hồi phục **{result.get('recovery_seconds', 0)}s** trước khi tiếp tục tu luyện."
                    ),
                    view=None,
                )
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _reject(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        self.stop()
        await interaction.response.edit_message(embed=success_embed("Đã từ chối đột phá", "Ngươi giữ nguyên cảnh giới và tiếp tục chuẩn bị."), view=None)

    async def _use_hint(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        await interaction.response.send_message(
            "Đan tăng tỷ lệ chỉ bị tiêu hao khi xác nhận đột phá. Vật phẩm hộ kiếp chỉ bị tiêu hao khi đột phá thành công và Cửu Lôi Kiếp thực sự bắt đầu.",
            ephemeral=True,
        )
