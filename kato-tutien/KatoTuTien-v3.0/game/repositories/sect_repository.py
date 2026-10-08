from __future__ import annotations

import time

from game.database.connection import Database
from game.models.sect import Sect, SectMember


class SectRepository:
    def __init__(self, db: Database):
        self.db = db

    def get(self, sect_id: str) -> Sect | None:
        row = self.db.fetchone("SELECT * FROM sects WHERE sect_id=?", (sect_id,))
        return Sect.from_row(row) if row else None

    def get_by_name(self, name: str) -> Sect | None:
        row = self.db.fetchone("SELECT * FROM sects WHERE name=?", (name,))
        return Sect.from_row(row) if row else None

    def list_all(self) -> list[Sect]:
        rows = self.db.fetchall("SELECT * FROM sects ORDER BY level DESC, exp DESC, name")
        return [Sect.from_row(r) for r in rows]


    def count(self) -> int:
        row = self.db.fetchone("SELECT COUNT(*) AS c FROM sects")
        return int(row["c"]) if row else 0

    def create(self, sect: Sect) -> None:
        self.db.execute(
            """INSERT INTO sects(sect_id, name, description, owner_id, level, exp, treasury, linh_mach_level, created_at)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (sect.sect_id, sect.name, sect.description, sect.owner_id, sect.level,
             sect.exp, sect.treasury, sect.linh_mach_level, sect.created_at),
        )

    def save(self, sect: Sect) -> None:
        self.db.execute(
            """UPDATE sects SET name=?, description=?, owner_id=?, level=?, exp=?,
               treasury=?, linh_mach_level=? WHERE sect_id=?""",
            (sect.name, sect.description, sect.owner_id, sect.level, sect.exp,
             sect.treasury, sect.linh_mach_level, sect.sect_id),
        )

    def delete(self, sect_id: str) -> None:
        for table in ("sect_members", "sect_applications", "sect_invitations", "sect_role_history"):
            self.db.execute(f"DELETE FROM {table} WHERE sect_id=?", (sect_id,))
        self.db.execute("DELETE FROM sects WHERE sect_id=?", (sect_id,))

    def get_member(self, sect_id: str, user_id: str) -> SectMember | None:
        row = self.db.fetchone(
            "SELECT * FROM sect_members WHERE sect_id=? AND user_id=?",
            (sect_id, user_id),
        )
        return SectMember.from_row(row) if row else None

    def get_member_by_user(self, user_id: str) -> SectMember | None:
        row = self.db.fetchone("SELECT * FROM sect_members WHERE user_id=?", (user_id,))
        return SectMember.from_row(row) if row else None

    def list_members(self, sect_id: str) -> list[SectMember]:
        rows = self.db.fetchall(
            "SELECT * FROM sect_members WHERE sect_id=? ORDER BY contribution DESC, joined_at ASC",
            (sect_id,),
        )
        return [SectMember.from_row(r) for r in rows]

    def add_member(self, member: SectMember) -> None:
        self.db.execute(
            """INSERT INTO sect_members(sect_id, user_id, role, contribution, joined_at)
               VALUES(?,?,?,?,?)""",
            (member.sect_id, member.user_id, member.role, member.contribution, member.joined_at),
        )

    def update_member(self, member: SectMember) -> None:
        self.db.execute(
            "UPDATE sect_members SET role=?, contribution=? WHERE sect_id=? AND user_id=?",
            (member.role, member.contribution, member.sect_id, member.user_id),
        )

    def remove_member(self, sect_id: str, user_id: str) -> None:
        self.db.execute(
            "DELETE FROM sect_members WHERE sect_id=? AND user_id=?",
            (sect_id, user_id),
        )

    def create_application(self, sect_id: str, user_id: str, message: str = "") -> int:
        cur = self.db.execute(
            "INSERT INTO sect_applications(sect_id, user_id, message, status, created_at) VALUES(?,?,?,?,?)",
            (sect_id, user_id, message, "pending", int(time.time())),
        )
        return int(cur.lastrowid)

    def has_pending_application(self, sect_id: str, user_id: str) -> bool:
        row = self.db.fetchone(
            "SELECT 1 FROM sect_applications WHERE sect_id=? AND user_id=? AND status='pending'",
            (sect_id, user_id),
        )
        return row is not None

    def list_applications(self, sect_id: str, status: str = "pending") -> list[dict]:
        rows = self.db.fetchall(
            "SELECT * FROM sect_applications WHERE sect_id=? AND status=? ORDER BY id",
            (sect_id, status),
        )
        return [dict(r) for r in rows]

    def set_application_status(self, app_id: int, status: str) -> None:
        self.db.execute("UPDATE sect_applications SET status=? WHERE id=?", (status, app_id))

    def create_invitation(self, sect_id: str, user_id: str, inviter_id: str) -> int:
        cur = self.db.execute(
            "INSERT INTO sect_invitations(sect_id, user_id, inviter_id, status, created_at) VALUES(?,?,?,?,?)",
            (sect_id, user_id, inviter_id, "pending", int(time.time())),
        )
        return int(cur.lastrowid)

    def has_pending_invitation(self, sect_id: str, user_id: str) -> bool:
        row = self.db.fetchone(
            "SELECT 1 FROM sect_invitations WHERE sect_id=? AND user_id=? AND status='pending'",
            (sect_id, user_id),
        )
        return row is not None

    def list_invitations(self, user_id: str, status: str = "pending") -> list[dict]:
        rows = self.db.fetchall(
            "SELECT * FROM sect_invitations WHERE user_id=? AND status=? ORDER BY id",
            (user_id, status),
        )
        return [dict(r) for r in rows]

    def set_invitation_status(self, inv_id: int, status: str) -> None:
        self.db.execute("UPDATE sect_invitations SET status=? WHERE id=?", (status, inv_id))

    def record_role_change(self, sect_id: str, actor_id: str, target_id: str, old_role: str, new_role: str) -> None:
        self.db.execute(
            """INSERT INTO sect_role_history(sect_id, actor_id, target_id, old_role, new_role, created_at)
               VALUES(?,?,?,?,?,?)""",
            (sect_id, actor_id, target_id, old_role, new_role, int(time.time())),
        )

    def role_history(self, sect_id: str, limit: int = 50) -> list[dict]:
        rows = self.db.fetchall(
            "SELECT * FROM sect_role_history WHERE sect_id=? ORDER BY id DESC LIMIT ?",
            (sect_id, max(1, min(limit, 100))),
        )
        return [dict(r) for r in rows]
