from __future__ import annotations

import discord
from game.services.errors import GameError
from ui.embeds import base_embed, error_embed, success_embed
from ui.views.quest_view import QuestOfferView, QuestChoiceView
from ui.views.quest_view import QuestMenuView
from ui.views.npc_view import NPCMenuView
from ui.views.world_view import WorldMenuView


async def cmd_npc(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    user_id = str(message.author.id)
    try:
        if not args:
            view = NPCMenuView(ctx.engine, user_id)
            await message.reply(embed=view.build_embed(), view=view)
            return
            npcs = ctx.engine.npc.list_npcs(user_id)
            if not npcs:
                await message.reply(embed=base_embed("👤 NPC", "Khu vực hiện tại chưa có người quen nào đáng chú ý."))
                return
            lines = [f"**{n['name']}** · {n['title']} · `{n['key']}`\n{n['description']}" for n in npcs]
            e = base_embed("👤 Người Trong Giang Hồ", "\n\n".join(lines))
            e.set_footer(text=".npc <mã> · Nói chuyện")
            await message.reply(embed=e)
            return
        r = ctx.engine.npc.talk(user_id, args[0].lower())
        npc = r["npc"]
        desc = f"**{npc['title']}**\n{npc['greeting']}"
        if r.get("memory"):
            desc += f"\n\n♡ Quan hệ: **{r['memory'].get('affinity', 0):+d}** · Gặp **{r['memory'].get('encounters', 0)}** lần"
        if r["quests"]:
            desc += "\n\n📜 Người này có chuyện muốn nhờ ngươi."
            await message.reply(embed=base_embed(f"👤 {npc['name']}", desc), view=QuestOfferView(ctx.engine, user_id, r["quests"]))
        else:
            desc += "\n\n*Hiện chưa có nhiệm vụ mới.*"
            await message.reply(embed=base_embed(f"👤 {npc['name']}", desc))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))


async def cmd_quest(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    user_id = str(message.author.id)
    try:
        if not args:
            view = QuestMenuView(ctx.engine, user_id)
            await message.reply(embed=view.build_embed(), view=view)
            return
            active = ctx.engine.quests.active(user_id)
            available = ctx.engine.quests.list_available(user_id)
            lines = []
            if active:
                lines.append("**ĐANG LÀM**")
                lines.extend(f"• **{item['quest']['name']}** — {item['step']['label']} · {item['row']['progress']}/{item['step'].get('amount', 1)}" for item in active)
            if available:
                lines.append("\n**CÓ THỂ NHẬN**")
                lines.extend(f"• `{item['key']}` · **{item['name']}** · {item['npc']}" for item in available)
            if not lines:
                lines.append("Chưa có nhiệm vụ. Hãy khám phá và gặp NPC.")
            e = base_embed("📜 Nhật Ký Nhiệm Vụ", "\n".join(lines))
            e.set_footer(text=".nhiemvu <mã> · Xem chi tiết")
            await message.reply(embed=e)
            return
        if args[0].lower() in ("nhan", "nhận") and len(args) > 1:
            r = ctx.engine.quests.start(user_id, args[1])
            await message.reply(embed=success_embed(f"📜 {r['quest']['name']}", f"Đã nhận nhiệm vụ.\n\n**Mục tiêu:** {r['step']['label']}"))
            return
        if args[0].lower() in ("chon", "chọn") and len(args) > 2:
            r = ctx.engine.quests.choose(user_id, args[1], args[2])
            text = r["choice"].get("effect", {}).get("text", "Quyết định của ngươi đã được ghi vào nhân sinh.")
            if r["changes"]:
                text += "\n\n" + "\n".join(f"• {x}" for x in r["changes"])
            await message.reply(embed=base_embed(f"📜 {r['quest']['name']}", text))
            return
        quest_key = args[0]
        r = ctx.engine.quests.status(user_id, quest_key)
        step = r["step"]
        text = f"{r['quest']['description']}\n\n**Mục tiêu hiện tại:** {step['label']}"
        if step.get("choices"):
            text += "\n\n⚖️ **Đây là một quyết định quan trọng.**"
            await message.reply(embed=base_embed(f"📜 {r['quest']['name']}", text), view=QuestChoiceView(ctx.engine, user_id, quest_key, step["choices"]))
            return
        text += f"\nTiến độ: {r['row']['progress']}/{step.get('amount', 1)}"
        await message.reply(embed=base_embed(f"📜 {r['quest']['name']}", text))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))


async def cmd_world(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    user_id = str(message.author.id)
    try:
        if not args:
            view = WorldMenuView(ctx.engine, user_id)
            await message.reply(embed=view.build_embed(), view=view)
            return
        events = ctx.engine.world.active()
        if args and args[0].lower() in ("thamgia", "tham_gia", "join") and len(args) > 1:
            r = ctx.engine.world.contribute(user_id, args[1])
            text = f"Ngươi đã góp sức cho **{r['event']['name']}**.\n\nTiến độ: **{r['progress']}/{r['target']}**\n🎁 Nhận: +{r['event']['reward']['stones']} linh thạch, +{r['event']['reward']['cultivation']} tu vi."
            if r["finished"]:
                text += "\n\n🌟 **Sự kiện thế giới đã kết thúc!**"
            await message.reply(embed=base_embed("🌍 Thế Giới", text))
            return
        if not events:
            await message.reply(embed=base_embed("🌍 Biến Động Thiên Hạ", "Thiên địa hiện đang yên tĩnh. Nhưng sự yên tĩnh này sẽ không kéo dài..."))
            return
        lines = []
        for e in events:
            remaining = max(0, int(e["expires_at"]) - __import__("time").time())
            mins = int(remaining // 60)
            lines.append(f"🌟 **{e['event_key']}** · {e['progress']}/{e['target']} · {mins} phút\nKhu: `{e['zone_key']}`")
        e = base_embed("🌍 Biến Động Thiên Hạ", "\n\n".join(lines))
        e.set_footer(text=".thegioi thamgia <mã> · Góp sức")
        await message.reply(embed=e)
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))
