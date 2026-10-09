from __future__ import annotations
import discord
from ui.theme.views import ThemedView
from game.services.errors import GameError
from ui.embeds import base_embed,error_embed,success_embed
from ui.emoji import EMOJI
class SectInviteNoticeView(ThemedView):
    def __init__(self, engine, user_id: str, invitation_id: int, timeout=300):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = str(user_id)
        self.invitation_id = int(invitation_id)
        ok = discord.ui.Button(label="Nhận lời mời", emoji=EMOJI["ok"], style=discord.ButtonStyle.success)
        no = discord.ui.Button(label="Từ chối", emoji=EMOJI["no"], style=discord.ButtonStyle.danger)
        ok.callback = self.accept
        no.callback = self.reject
        self.add_item(ok); self.add_item(no)

    @staticmethod
    def build_embed(engine, invitation_id: int):
        inv = engine.sect.invitation_info(invitation_id)
        if not inv:
            return base_embed("🏯 Lời mời", "Lời mời không còn tồn tại.")
        return base_embed("🏯 Lời mời tông môn", f"**{inv['sect_name']}** mời ngươi gia nhập.\nNgười gửi: <@{inv['inviter_id']}>\nMã: **#{invitation_id}**")

    async def accept(self, i):
        if str(i.user.id) != self.user_id:
            return await i.response.send_message("Lời mời này không thuộc về ngươi.", ephemeral=True)
        try:
            self.engine.sect.accept_invite(self.user_id, self.invitation_id)
            await i.response.edit_message(embed=success_embed("🏯 Tông Môn", "Đã nhận lời mời."), view=None)
        except GameError as e:
            await i.response.send_message(embed=error_embed(str(e)), ephemeral=True)

    async def reject(self, i):
        if str(i.user.id) != self.user_id:
            return await i.response.send_message("Lời mời này không thuộc về ngươi.", ephemeral=True)
        try:
            self.engine.sect.reject_invite(self.user_id, self.invitation_id)
            await i.response.edit_message(embed=base_embed("🏯 Lời mời", "Đã từ chối lời mời."), view=None)
        except GameError as e:
            await i.response.send_message(embed=error_embed(str(e)), ephemeral=True)


class SectManagementView(ThemedView):
    def __init__(self,engine,user_id,timeout=300):
        super().__init__(timeout=timeout); self.engine=engine; self.user_id=user_id; self.app=None; self.inv=None; self.build()
    def guard(self,i): return str(i.user.id)==self.user_id
    def build(self):
        self.clear_items(); ov=self.engine.sect.overview(self.user_id); apps=ov.get("applications",[]); invs=ov.get("invitations",[])
        if apps:
            app_options = []
            for a in apps[:25]:
                player = self.engine.players.get(str(a["user_id"]))
                name = (player.display_name if player and player.display_name else f"Người chơi {str(a['user_id'])[-4:]}").strip()
                app_options.append(discord.SelectOption(label=f"{name}"[:100], description=f"Đơn #{a['id']}", value=str(a['id'])))
            x=discord.ui.Select(placeholder="Chọn người xin gia nhập…",options=app_options,row=0); x.callback=self.sel_app; self.add_item(x)
            ok=discord.ui.Button(label="Duyệt",emoji=EMOJI['ok'],style=discord.ButtonStyle.success,row=1); no=discord.ui.Button(label="Từ chối",emoji=EMOJI['no'],style=discord.ButtonStyle.danger,row=1); ok.callback=self.accept_app; no.callback=self.reject_app; self.add_item(ok); self.add_item(no)
        if invs:
            x=discord.ui.Select(placeholder="Chọn lời mời…",options=[discord.SelectOption(label=f"#{a['id']} · {a['sect_id']}",value=str(a['id'])) for a in invs[:25]],row=2); x.callback=self.sel_inv; self.add_item(x)
            ok=discord.ui.Button(label="Nhận lời mời",emoji=EMOJI['ok'],style=discord.ButtonStyle.success,row=3); no=discord.ui.Button(label="Từ chối",emoji=EMOJI['no'],style=discord.ButtonStyle.danger,row=3); ok.callback=self.accept_inv; no.callback=self.reject_inv; self.add_item(ok); self.add_item(no)
        back=discord.ui.Button(label="Quay lại",style=discord.ButtonStyle.secondary,row=4); back.callback=self.back; self.add_item(back)
    def build_embed(self):
        ov = self.engine.sect.overview(self.user_id)
        text = (
            f"Đơn chờ: **{len(ov.get('applications', []))}**\n"
            f"Lời mời: **{len(ov.get('invitations', []))}**"
        )
        return base_embed("🏯 Quản lý tông môn", text)

    async def sel_app(self,i):
        if not self.guard(i): return await i.response.send_message("Giao diện này không thuộc về ngươi.",ephemeral=True)
        self.app=int(i.data['values'][0]); await i.response.edit_message(embed=self.build_embed(),view=self)
    async def sel_inv(self,i):
        if not self.guard(i): return await i.response.send_message("Giao diện này không thuộc về ngươi.",ephemeral=True)
        self.inv=int(i.data['values'][0]); await i.response.edit_message(embed=self.build_embed(),view=self)
    async def accept_app(self,i):
        if not self.guard(i): return await i.response.send_message("Giao diện này không thuộc về ngươi.",ephemeral=True)
        if self.app is None: return await i.response.send_message("Hãy chọn một đơn trước.",ephemeral=True)
        try: self.engine.sect.accept_application(self.user_id,self.app); self.build(); await i.response.edit_message(embed=success_embed("🏯 Tông Môn","Đã duyệt đơn."),view=self)
        except GameError as e: await i.response.send_message(embed=error_embed(str(e)),ephemeral=True)
    async def reject_app(self,i):
        if not self.guard(i): return await i.response.send_message("Giao diện này không thuộc về ngươi.",ephemeral=True)
        if self.app is None: return await i.response.send_message("Hãy chọn một đơn trước.",ephemeral=True)
        try: self.engine.sect.reject_application(self.user_id,self.app); self.build(); await i.response.edit_message(embed=base_embed("🏯 Tông Môn","Đã từ chối đơn."),view=self)
        except GameError as e: await i.response.send_message(embed=error_embed(str(e)),ephemeral=True)
    async def accept_inv(self,i):
        if not self.guard(i): return await i.response.send_message("Giao diện này không thuộc về ngươi.",ephemeral=True)
        if self.inv is None: return await i.response.send_message("Hãy chọn một lời mời trước.",ephemeral=True)
        try: self.engine.sect.accept_invite(self.user_id,self.inv); self.build(); await i.response.edit_message(embed=success_embed("🏯 Tông Môn","Đã gia nhập tông môn."),view=self)
        except GameError as e: await i.response.send_message(embed=error_embed(str(e)),ephemeral=True)
    async def reject_inv(self,i):
        if not self.guard(i): return await i.response.send_message("Giao diện này không thuộc về ngươi.",ephemeral=True)
        if self.inv is None: return await i.response.send_message("Hãy chọn một lời mời trước.",ephemeral=True)
        try: self.engine.sect.reject_invite(self.user_id,self.inv); self.build(); await i.response.edit_message(embed=base_embed("🏯 Lời mời","Đã từ chối."),view=self)
        except GameError as e: await i.response.send_message(embed=error_embed(str(e)),ephemeral=True)
    async def back(self,i):
        if not self.guard(i): return await i.response.send_message("Giao diện này không thuộc về ngươi.",ephemeral=True)
        from ui.views.sect_view import SectMenuView
        v=SectMenuView(self.engine,self.user_id); await i.response.edit_message(embed=v.build_embed(),view=v)
