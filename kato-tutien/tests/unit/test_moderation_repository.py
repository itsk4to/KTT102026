from __future__ import annotations

from game.database.connection import Database
from game.database.migrations import run_migrations
from game.database.schema import SCHEMA_VERSION
from game.moderation.service import ModerationService


def test_schema_migrates_and_records_a_manual_moderation_case():
    db = Database(":memory:")
    try:
        assert run_migrations(db) == 18
        assert SCHEMA_VERSION == 18
        service = ModerationService(db)
        case = service.record_action(
            guild_id="guild-1",
            moderator_id="mod-1",
            target_id="member-1",
            target_type="user",
            action="warn",
            reason="Invite spam",
            created_at=1_800_000_000,
        )

        assert case["case_id"] == 1
        assert case["guild_id"] == "guild-1"
        assert case["action"] == "warn"
        assert service.count_warnings("guild-1", "member-1") == 1
        assert service.count_warnings("guild-2", "member-1") == 0
    finally:
        db.close()


def test_case_history_is_scoped_to_guild_and_target():
    db = Database(":memory:")
    try:
        run_migrations(db)
        service = ModerationService(db)
        first = service.record_action(
            guild_id="guild-1",
            moderator_id="mod-1",
            target_id="member-1",
            target_type="user",
            action="timeout",
            reason="Repeated disruption",
            expires_at=1_800_000_600,
            created_at=1_800_000_000,
        )
        service.record_action(
            guild_id="guild-2",
            moderator_id="mod-2",
            target_id="member-1",
            target_type="user",
            action="warn",
            reason="Different server",
            created_at=1_800_000_001,
        )

        assert service.get_case("guild-1", first["case_id"])["reason"] == "Repeated disruption"
        assert service.get_case("guild-2", first["case_id"]) is None
        assert len(service.recent_cases("guild-1", target_id="member-1")) == 1
        assert len(service.recent_cases("guild-1")) == 1
    finally:
        db.close()


def test_latest_channel_lock_event_is_guild_scoped_and_tracks_unlock():
    db = Database(":memory:")
    try:
        run_migrations(db)
        service = ModerationService(db)
        lock_case = service.record_action(
            guild_id="guild-1",
            moderator_id="mod-1",
            target_id="channel-1",
            target_type="channel",
            action="lock",
            reason="Raid prevention",
            details='{"previous_send_messages":null}',
            created_at=1_800_000_000,
        )
        assert service.latest_channel_lock_event("guild-1", "channel-1")["case_id"] == lock_case["case_id"]
        assert service.latest_channel_lock_event("guild-2", "channel-1") is None

        unlock_case = service.record_action(
            guild_id="guild-1",
            moderator_id="mod-1",
            target_id="channel-1",
            target_type="channel",
            action="unlock",
            reason="Raid ended",
            created_at=1_800_000_100,
        )
        latest = service.latest_channel_lock_event("guild-1", "channel-1")
        assert latest["case_id"] == unlock_case["case_id"]
        assert latest["action"] == "unlock"
    finally:
        db.close()
