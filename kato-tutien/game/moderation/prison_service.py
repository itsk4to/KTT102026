"""Use cases for Heavenly Dao prison labour and community rewards."""
from __future__ import annotations

from typing import Any

from game.database.connection import Database
from game.moderation.prison_repository import PrisonError, PrisonRepository


class PrisonService:
    def __init__(self, db: Database):
        self.repository = PrisonRepository(db)

    def create_session(self, **kwargs: Any) -> dict[str, Any]:
        return self.repository.create_session(**kwargs)

    def get_active_session(self, guild_id: str, user_id: str) -> dict[str, Any] | None:
        return self.repository.get_active_session(guild_id, user_id)

    def get_active_session_for_user(self, user_id: str) -> dict[str, Any] | None:
        return self.repository.get_active_session_for_user(user_id)

    def get_session(self, session_id: int) -> dict[str, Any] | None:
        return self.repository.get_session(session_id)

    def set_permission_snapshot(self, session_id: int, snapshot: dict[str, Any]) -> None:
        self.repository.set_permission_snapshot(session_id, snapshot)

    def permission_snapshot(self, session: dict[str, Any]) -> dict[str, Any]:
        return self.repository.permission_snapshot(session)

    def activate(self, session_id: int) -> None:
        self.repository.activate(session_id)

    def mark_failed(self, session_id: int, error: str) -> None:
        self.repository.mark_failed(session_id, error)

    def mine(self, **kwargs: Any) -> dict[str, Any]:
        return self.repository.mine(**kwargs)

    def request_release(self, session_id: int) -> dict[str, Any]:
        return self.repository.request_release(session_id)

    def finalize_payout(self, session_id: int) -> dict[str, Any]:
        return self.repository.finalize_payout(session_id)

    def get_payout_items(self, payout_id: int) -> list[dict[str, Any]]:
        return self.repository.get_payout_items(payout_id)

    def get_pending_releases(self) -> list[dict[str, Any]]:
        return self.repository.get_pending_releases()

    def get_preparing_sessions(self) -> list[dict[str, Any]]:
        return self.repository.get_preparing_sessions()

    def mark_announcement_sent(self, session_id: int) -> None:
        self.repository.mark_announcement_sent(session_id)


    def get_unannounced_completed(self) -> list[dict[str, Any]]:
        return self.repository.get_unannounced_completed()


__all__ = ["PrisonService", "PrisonError"]
