"""Persistence for Discord moderation cases.

This repository deliberately uses tables separate from the in-game
``admin_audit`` table. Moderation records are scoped by guild so a future
multi-server deployment cannot mix records between servers.
"""
from __future__ import annotations

import time
from typing import Any

from game.database.connection import Database


class ModerationRepository:
    def __init__(self, db: Database):
        self.db = db

    def create_case(
        self,
        *,
        guild_id: str,
        moderator_id: str,
        target_id: str,
        target_type: str,
        action: str,
        reason: str,
        expires_at: int | None = None,
        details: str = "",
        created_at: int | None = None,
    ) -> dict[str, Any]:
        """Persist one successful manual action and return its case record."""
        now = int(time.time()) if created_at is None else int(created_at)
        cursor = self.db.execute(
            """INSERT INTO moderation_cases (
                guild_id, moderator_id, target_id, target_type, action,
                reason, created_at, expires_at, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                str(guild_id),
                str(moderator_id),
                str(target_id),
                str(target_type),
                str(action).lower(),
                str(reason)[:500],
                now,
                int(expires_at) if expires_at is not None else None,
                str(details)[:1000],
            ),
        )
        case = self.get_case(str(guild_id), int(cursor.lastrowid))
        if case is None:  # Defensive: the insert should always be readable.
            raise RuntimeError("Moderation case was saved but could not be fetched")
        return case

    def get_case(self, guild_id: str, case_id: int) -> dict[str, Any] | None:
        row = self.db.fetchone(
            "SELECT * FROM moderation_cases WHERE guild_id=? AND case_id=?",
            (str(guild_id), int(case_id)),
        )
        return dict(row) if row is not None else None

    def count_warnings(self, guild_id: str, target_id: str) -> int:
        row = self.db.fetchone(
            """SELECT COUNT(*) AS total FROM moderation_cases
               WHERE guild_id=? AND target_id=? AND target_type='user' AND action='warn'""",
            (str(guild_id), str(target_id)),
        )
        return int(row["total"]) if row is not None else 0

    def list_warnings(
        self, guild_id: str, target_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 50))
        rows = self.db.fetchall(
            """SELECT * FROM moderation_cases
               WHERE guild_id=? AND target_id=? AND target_type='user' AND action='warn'
               ORDER BY case_id DESC LIMIT ?""",
            (str(guild_id), str(target_id), safe_limit),
        )
        return [dict(row) for row in rows]

    def latest_channel_lock_event(
        self, guild_id: str, channel_id: str
    ) -> dict[str, Any] | None:
        """Return the newest lock/unlock event for a channel in one guild."""
        row = self.db.fetchone(
            """SELECT * FROM moderation_cases
               WHERE guild_id=? AND target_id=? AND target_type='channel'
                 AND action IN ('lock', 'unlock')
               ORDER BY case_id DESC LIMIT 1""",
            (str(guild_id), str(channel_id)),
        )
        return dict(row) if row is not None else None

    def recent_cases(
        self,
        guild_id: str,
        *,
        target_id: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        safe_limit = max(1, min(int(limit), 50))
        if target_id is None:
            rows = self.db.fetchall(
                """SELECT * FROM moderation_cases WHERE guild_id=?
                   ORDER BY case_id DESC LIMIT ?""",
                (str(guild_id), safe_limit),
            )
        else:
            rows = self.db.fetchall(
                """SELECT * FROM moderation_cases WHERE guild_id=? AND target_id=?
                   ORDER BY case_id DESC LIMIT ?""",
                (str(guild_id), str(target_id), safe_limit),
            )
        return [dict(row) for row in rows]
