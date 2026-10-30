"""Application service for recording and querying moderation cases."""
from __future__ import annotations

from typing import Any

from game.database.connection import Database
from game.moderation.repository import ModerationRepository


class ModerationService:
    """Thin service facade; Discord API calls remain in the UI adapter."""

    def __init__(self, db: Database):
        self.repository = ModerationRepository(db)

    def record_action(self, **case_data: Any) -> dict[str, Any]:
        return self.repository.create_case(**case_data)

    def get_case(self, guild_id: str, case_id: int) -> dict[str, Any] | None:
        return self.repository.get_case(guild_id, case_id)

    def count_warnings(self, guild_id: str, target_id: str) -> int:
        return self.repository.count_warnings(guild_id, target_id)

    def list_warnings(
        self, guild_id: str, target_id: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        return self.repository.list_warnings(guild_id, target_id, limit)

    def latest_channel_lock_event(
        self, guild_id: str, channel_id: str
    ) -> dict[str, Any] | None:
        return self.repository.latest_channel_lock_event(guild_id, channel_id)

    def recent_cases(
        self,
        guild_id: str,
        *,
        target_id: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return self.repository.recent_cases(
            guild_id, target_id=target_id, limit=limit
        )
