from __future__ import annotations

import time
import uuid

from game.content.sects_content import SECT_ROLES
from game.models.sect import Sect, SectMember
from game.repositories.player_repository import PlayerRepository
from game.repositories.sect_repository import SectRepository
from game.rules.sect_rules import can_change_role, can_kick, has_permission
from game.services.errors import GameError


class SectService:
    def __init__(self, players: PlayerRepository, sects: SectRepository):
        self.players = players
        self.sects = sects

    def _require_player(self, user_id: str):
        p = self.players.get(user_id)
        if not p:
            raise GameError("Ngươi chưa bước lên con đường tu hành.")
        return p

    def _require_member(self, user_id: str):
        p = self._require_player(user_id)
        if not p.sect_id:
            raise GameError("Ngươi không ở tông môn.")
        member = self.sects.get_member(p.sect_id, user_id)
        if not member:
            raise GameError("Dữ liệu tông môn không hợp lệ.")
        return p, member

    def list_sects(self) -> list[dict]:
        return [
            {"sect_id": s.sect_id, "name": s.name, "level": s.level, "treasury": s.treasury, "owner_id": s.owner_id}
            for s in self.sects.list_all()
        ]

    def create(self, user_id: str, name: str, description: str = "") -> dict:
        p = self._require_player(user_id)
        if p.sect_id:
            raise GameError("Đã ở trong tông môn.")
        name = name.strip()[:32]
        if len(name) < 2:
            raise GameError("Tên tông môn quá ngắn.")
        if self.sects.get_by_name(name):
            raise GameError("Tên tông môn đã tồn tại.")
        if p.spirit_stones < 10_000:
            raise GameError("Cần 10.000 linh thạch để sáng lập.")
        sid = uuid.uuid4().hex[:12]
        sect = Sect(
            sect_id=sid,
            name=name,
            description=description[:200],
            owner_id=user_id,
            created_at=int(time.time()),
        )
        member = SectMember(sect_id=sid, user_id=user_id, role="Tông Chủ", joined_at=int(time.time()))
        with self.players.transaction():
            p.spirit_stones -= 10_000
            self.sects.create(sect)
            self.sects.add_member(member)
            p.sect_id = sid
            self.players.save(p)
        return {"sect": sect, "player": p}

    def apply(self, user_id: str, sect_id: str, message: str = "") -> dict:
        p = self._require_player(user_id)
        if p.sect_id:
            raise GameError("Đã ở trong tông môn.")
        sect = self.sects.get(sect_id)
        if not sect:
            raise GameError("Tông môn không tồn tại.")
        if self.sects.has_pending_application(sect_id, user_id):
            raise GameError("Đã có đơn đang chờ duyệt.")
        app_id = self.sects.create_application(sect_id, user_id, message[:200])
        return {"application_id": app_id, "sect": sect}

    def accept_application(self, actor_id: str, app_id: int) -> dict:
        actor, member = self._require_member(actor_id)
        if not has_permission(member.role, "sect.accept_application"):
            raise GameError("Không có quyền duyệt.")
        apps = self.sects.list_applications(actor.sect_id)
        app = next((a for a in apps if a["id"] == app_id), None)
        if not app:
            raise GameError("Đơn không tồn tại.")
        target = self.players.get(app["user_id"])
        if not target:
            raise GameError("Người xin không tồn tại.")
        if target.sect_id:
            self.sects.set_application_status(app_id, "rejected")
            raise GameError("Người này đã có tông môn.")
        with self.players.transaction():
            self.sects.set_application_status(app_id, "accepted")
            self.sects.add_member(SectMember(
                sect_id=actor.sect_id,
                user_id=target.user_id,
                role="Ngoại Môn Đệ Tử",
                joined_at=int(time.time()),
            ))
            target.sect_id = actor.sect_id
            self.players.save(target)
        return {"user_id": target.user_id, "sect_id": actor.sect_id}

    def reject_application(self, actor_id: str, app_id: int) -> dict:
        actor, member = self._require_member(actor_id)
        if not has_permission(member.role, "sect.accept_application"): raise GameError("Không có quyền xử lý đơn.")
        app = next((a for a in self.sects.list_applications(actor.sect_id) if a["id"] == app_id), None)
        if not app: raise GameError("Đơn không tồn tại.")
        self.sects.set_application_status(app_id,"rejected"); return {"user_id":app["user_id"]}

    def reject_invite(self,user_id: str,inv_id: int)->dict:
        self._require_player(user_id); inv=next((x for x in self.sects.list_invitations(user_id) if x["id"]==inv_id),None)
        if not inv: raise GameError("Lời mời không tồn tại.")
        self.sects.set_invitation_status(inv_id,"rejected"); return inv

    def invite(self, actor_id: str, target_id: str) -> dict:
        actor, member = self._require_member(actor_id)
        if not has_permission(member.role, "sect.invite"):
            raise GameError("Không có quyền mời.")
        if actor_id == target_id:
            raise GameError("Không thể tự mời mình.")
        target = self.players.get(target_id)
        if not target:
            raise GameError("Người được mời chưa khai đạo.")
        if target.sect_id:
            raise GameError("Đối phương đã có tông môn.")
        if self.sects.has_pending_invitation(actor.sect_id, target_id):
            raise GameError("Đã có lời mời đang chờ.")
        inv_id = self.sects.create_invitation(actor.sect_id, target_id, actor_id)
        return {"invitation_id": inv_id}

    def cancel_invite(self, actor_id: str, inv_id: int) -> dict:
        actor, member = self._require_member(actor_id)
        if not has_permission(member.role, "sect.invite"):
            raise GameError("Không có quyền hủy lời mời.")
        inv = self.invitation_info(inv_id)
        if not inv or inv["sect_id"] != actor.sect_id or inv["status"] != "pending":
            raise GameError("Lời mời không tồn tại.")
        self.sects.set_invitation_status(inv_id, "cancelled")
        return inv

    def accept_invite(self, user_id: str, inv_id: int) -> dict:
        p = self._require_player(user_id)
        if p.sect_id:
            raise GameError("Đã ở tông môn.")
        invs = self.sects.list_invitations(user_id)
        inv = next((i for i in invs if i["id"] == inv_id), None)
        if not inv:
            raise GameError("Lời mời không tồn tại.")
        sect = self.sects.get(inv["sect_id"])
        if not sect:
            raise GameError("Tông môn không còn tồn tại.")
        with self.players.transaction():
            self.sects.set_invitation_status(inv_id, "accepted")
            self.sects.add_member(SectMember(
                sect_id=inv["sect_id"],
                user_id=user_id,
                role="Ngoại Môn Đệ Tử",
                joined_at=int(time.time()),
            ))
            p.sect_id = inv["sect_id"]
            self.players.save(p)
        return {"sect_id": inv["sect_id"], "player": p}

    def contribute(self, user_id: str, amount: int) -> dict:
        if amount < 1:
            raise GameError("Số lượng phải > 0.")
        p, member = self._require_member(user_id)
        if p.spirit_stones < amount:
            raise GameError("Không đủ linh thạch.")
        sect = self.sects.get(p.sect_id)
        if not sect:
            raise GameError("Tông môn không tồn tại.")
        with self.players.transaction():
            p.spirit_stones -= amount
            sect.treasury += amount
            member.contribution += amount
            self.players.save(p)
            self.sects.save(sect)
            self.sects.update_member(member)
        if getattr(self, "sect_tower", None) is not None:
            self.sect_tower.record_activity(user_id, "donate", amount)
        return {"amount": amount, "treasury": sect.treasury, "contribution": member.contribution}

    def leave(self, user_id: str) -> dict:
        p, member = self._require_member(user_id)
        if member.role == "Tông Chủ":
            raise GameError("Tông Chủ phải nhường chức hoặc giải tán trước.")
        with self.players.transaction():
            self.sects.remove_member(p.sect_id, user_id)
            p.sect_id = None
            self.players.save(p)
        return {"player": p}

    def dissolve(self, user_id: str) -> dict:
        p, member = self._require_member(user_id)
        if not has_permission(member.role, "sect.dissolve"):
            raise GameError("Chỉ Tông Chủ mới giải tán được.")
        members = self.sects.list_members(p.sect_id)
        with self.players.transaction():
            for m in members:
                mp = self.players.get(m.user_id)
                if mp:
                    mp.sect_id = None
                    self.players.save(mp)
            self.sects.delete(p.sect_id)
        return {"ok": True}

    def invitation_info(self, invitation_id: int) -> dict | None:
        data = self.sects.get_invitation(invitation_id)
        if not data:
            return None
        sect = self.sects.get(data["sect_id"])
        data["sect_name"] = sect.name if sect else "một tông môn"
        return data

    def overview(self, user_id: str) -> dict:
        p = self._require_player(user_id)
        if not p.sect_id:
            return {"in_sect": False, "sects": self.list_sects(), "invitations": self.sects.list_invitations(user_id)}
        sect = self.sects.get(p.sect_id)
        members = self.sects.list_members(p.sect_id)
        member = self.sects.get_member(p.sect_id, user_id)
        apps = self.sects.list_applications(p.sect_id) if member and has_permission(member.role, "sect.accept_application") else []
        invites = self.sects.list_invitations(user_id)
        return {
            "in_sect": True,
            "sect": sect,
            "members": members,
            "my_role": member.role if member else None,
            "applications": apps,
            "invitations": invites,
            "role_history": self.sects.role_history(p.sect_id),
        }

    def change_role(self, actor_id: str, target_id: str, new_role: str) -> dict:
        if new_role not in SECT_ROLES:
            raise GameError("Chức vụ không hợp lệ.")
        actor, am = self._require_member(actor_id)
        tm = self.sects.get_member(actor.sect_id, target_id)
        if not tm:
            raise GameError("Không phải thành viên.")
        if target_id == actor_id:
            raise GameError("Không thể tự đổi chức vụ.")
        old_role = tm.role
        promote = SECT_ROLES.index(new_role) < SECT_ROLES.index(old_role)
        if not can_change_role(am.role, old_role, new_role, promote=promote):
            raise GameError("Không đủ thẩm quyền thay đổi chức vụ này.")
        with self.players.transaction():
            tm.role = new_role
            self.sects.update_member(tm)
            self.sects.record_role_change(actor.sect_id, actor_id, target_id, old_role, new_role)
        return {"user_id": target_id, "old_role": old_role, "role": new_role}

    def kick(self, actor_id: str, target_id: str) -> dict:
        actor, am = self._require_member(actor_id)
        if actor_id == target_id:
            raise GameError("Không thể tự khai trừ.")
        target = self.players.get(target_id)
        tm = self.sects.get_member(actor.sect_id, target_id)
        if not target or not tm:
            raise GameError("Không phải thành viên.")
        if not can_kick(am.role, tm.role):
            raise GameError("Không đủ thẩm quyền khai trừ người này.")
        with self.players.transaction():
            self.sects.remove_member(actor.sect_id, target_id)
            target.sect_id = None
            self.players.save(target)
        return {"user_id": target_id}

    def transfer_leadership(self, actor_id: str, target_id: str) -> dict:
        actor, am = self._require_member(actor_id)
        if am.role != "Tông Chủ":
            raise GameError("Chỉ Tông Chủ mới có thể nhường chức.")
        target = self.sects.get_member(actor.sect_id, target_id)
        if not target or target_id == actor_id:
            raise GameError("Người nhận chức không hợp lệ.")
        old_role = target.role
        with self.players.transaction():
            actor.role = "Phó Tông Chủ"
            target.role = "Tông Chủ"
            self.sects.update_member(actor)
            self.sects.update_member(target)
            self.sects.record_role_change(actor.sect_id, actor_id, target_id, old_role, "Tông Chủ")
            self.sects.record_role_change(actor.sect_id, actor_id, actor_id, "Tông Chủ", "Phó Tông Chủ")
            sect = self.sects.get(actor.sect_id)
            sect.owner_id = target_id
            self.sects.save(sect)
        return {"new_owner_id": target_id, "old_owner_id": actor_id}
