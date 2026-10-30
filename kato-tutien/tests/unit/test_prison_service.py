from __future__ import annotations

import pytest

from game.database.connection import Database
from game.database.migrations import run_migrations
from game.database.schema import SCHEMA_VERSION
from game.moderation.prison_repository import PrisonError
from game.moderation.prison_service import PrisonService


def _db_with_players(*user_ids: str) -> Database:
    db = Database(":memory:")
    run_migrations(db)
    for user_id in user_ids:
        db.execute(
            "INSERT INTO players(user_id,display_name,spirit_stones) VALUES(?,?,100)",
            (user_id, user_id),
        )
    return db


def _active_session(service: PrisonService, user_id: str, *, required: int = 10, guild: str = "g1"):
    session = service.create_session(
        guild_id=guild, user_id=user_id, actor_id="admin", required_stones=required,
        reason="test", now=100,
    )
    service.set_permission_snapshot(session["session_id"], {"channels": {}})
    service.activate(session["session_id"])
    return service.get_session(session["session_id"])


def test_schema_18_migrates_and_prison_mining_is_exactly_ten():
    db = _db_with_players("prisoner", "recipient")
    try:
        assert SCHEMA_VERSION == 18
        assert run_migrations(db) == 18
        service = PrisonService(db)
        session = _active_session(service, "prisoner", required=15)

        first = service.mine(
            guild_id="g1", user_id="prisoner", channel_id="jail", expected_channel_id="jail",
            event_id="message-1", cooldown_seconds=0, now=200,
        )
        assert first["amount"] == 10
        assert first["total_stones"] == 10
        assert first["remaining_stones"] == 5
        assert first["release_due"] is False

        second = service.mine(
            guild_id="g1", user_id="prisoner", channel_id="jail", expected_channel_id="jail",
            event_id="message-2", cooldown_seconds=0, now=201,
        )
        assert second["amount"] == 10
        assert second["total_stones"] == 20
        assert second["release_due"] is True
        assert db.fetchone("SELECT spirit_stones FROM players WHERE user_id='prisoner'")["spirit_stones"] == 100
        assert service.get_session(session["session_id"])["status"] == "release_pending"
    finally:
        db.close()


def test_mining_rejects_duplicates_cooldown_and_wrong_channel():
    db = _db_with_players("prisoner")
    try:
        service = PrisonService(db)
        _active_session(service, "prisoner", required=100)
        kwargs = dict(
            guild_id="g1", user_id="prisoner", channel_id="jail", expected_channel_id="jail",
            cooldown_seconds=30, now=200,
        )
        service.mine(event_id="message-1", **kwargs)
        with pytest.raises(PrisonError, match="đã được ghi nhận"):
            service.mine(event_id="message-1", **{**kwargs, "now": 231})
        with pytest.raises(PrisonError, match="hồi sức"):
            service.mine(event_id="message-2", **{**kwargs, "now": 220})
        with pytest.raises(PrisonError, match="kênh lao ngục"):
            service.mine(event_id="message-3", **{**kwargs, "channel_id": "general", "now": 240})
    finally:
        db.close()


def test_payout_excludes_all_prisoners_and_is_idempotent():
    db = _db_with_players("released-prisoner", "other-prisoner", "p3", "p4", "p5")
    try:
        service = PrisonService(db)
        released = _active_session(service, "released-prisoner", required=10)
        _active_session(service, "other-prisoner", required=500)
        mined = service.mine(
            guild_id="g1", user_id="released-prisoner", channel_id="jail", expected_channel_id="jail",
            event_id="release-message", cooldown_seconds=0, now=200,
        )
        assert mined["release_due"] is True
        service.finalize_payout(released["session_id"])
        payout = service.finalize_payout(released["session_id"])
        assert payout["total_stones"] == 10
        assert payout["recipient_count"] == 4
        assert payout["per_player_reward"] == 2
        assert payout["remainder"] == 2
        assert db.fetchone("SELECT spirit_stones FROM players WHERE user_id='released-prisoner'")["spirit_stones"] == 102
        assert db.fetchone("SELECT spirit_stones FROM players WHERE user_id='other-prisoner'")["spirit_stones"] == 100
        for user_id in ("p3", "p4", "p5"):
            assert db.fetchone("SELECT spirit_stones FROM players WHERE user_id=?", (user_id,))["spirit_stones"] == 102
        assert db.fetchone("SELECT spirit_stones FROM community_fund WHERE fund_id=1")["spirit_stones"] == 2
        assert db.fetchone("SELECT COUNT(*) AS c FROM prison_payouts")["c"] == 1
    finally:
        db.close()


def test_empty_recipient_list_keeps_entire_reward_in_community_fund():
    db = _db_with_players("other-prisoner")
    try:
        service = PrisonService(db)
        session = service.create_session(
            guild_id="g1", user_id="unregistered-prisoner", actor_id="admin",
            required_stones=10, reason="manual release", now=100,
        )
        service.set_permission_snapshot(session["session_id"], {"channels": {}})
        service.activate(session["session_id"])
        _active_session(service, "other-prisoner", required=100)
        # A manually settled case can carry a previously recorded labour total
        # even when the target never created a game profile.
        db.execute(
            "UPDATE prison_sessions SET total_stones=10,status='release_pending' WHERE session_id=?",
            (session["session_id"],),
        )
        payout = service.finalize_payout(session["session_id"])
        assert payout["recipient_count"] == 0
        assert payout["per_player_reward"] == 0
        assert payout["remainder"] == 10
        assert db.fetchone("SELECT spirit_stones FROM community_fund WHERE fund_id=1")["spirit_stones"] == 10
        assert db.fetchone("SELECT spirit_stones FROM players WHERE user_id='other-prisoner'")["spirit_stones"] == 100
    finally:
        db.close()


def test_unregistered_member_can_be_jailed_but_must_register_before_mining():
    db = _db_with_players("recipient")
    try:
        service = PrisonService(db)
        session = service.create_session(
            guild_id="g1", user_id="not-registered-yet", actor_id="admin",
            required_stones=10, reason="test", now=100,
        )
        service.set_permission_snapshot(session["session_id"], {"channels": {}})
        service.activate(session["session_id"])
        with pytest.raises(PrisonError, match="đăng ký nhân vật"):
            service.mine(
                guild_id="g1", user_id="not-registered-yet", channel_id="jail",
                expected_channel_id="jail", event_id="before-register",
                cooldown_seconds=30, now=200,
            )
        db.execute(
            "INSERT INTO players(user_id,display_name,spirit_stones) VALUES(?,?,100)",
            ("not-registered-yet", "New Player"),
        )
        result = service.mine(
            guild_id="g1", user_id="not-registered-yet", channel_id="jail",
            expected_channel_id="jail", event_id="after-register",
            cooldown_seconds=30, now=201,
        )
        assert result["amount"] == 10
        assert result["release_due"] is True
    finally:
        db.close()


def test_schema_16_upgrade_preserves_existing_player_and_creates_moderation_prison_tables():
    db = _db_with_players("legacy-player")
    try:
        db.execute("UPDATE players SET spirit_stones=765432 WHERE user_id='legacy-player'")
        db.execute("UPDATE schema_meta SET value='16' WHERE key='version'")
        assert run_migrations(db) == 18
        assert db.fetchone("SELECT spirit_stones FROM players WHERE user_id='legacy-player'")["spirit_stones"] == 765432
        for table in ("moderation_cases", "prison_sessions", "prison_mining_events", "prison_payouts", "community_fund"):
            assert db.fetchone("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)) is not None
        assert db.fetchone("SELECT value FROM schema_meta WHERE key='version'")["value"] == "18"
    finally:
        db.close()


def test_prison_state_is_global_for_access_gate_and_prevents_parallel_sentences():
    db = _db_with_players("prisoner")
    try:
        service = PrisonService(db)
        session = _active_session(service, "prisoner", required=100, guild="guild-a")
        assert service.get_active_session_for_user("prisoner")["session_id"] == session["session_id"]
        with pytest.raises(PrisonError, match="phiên tù chưa hoàn tất"):
            service.create_session(
                guild_id="guild-b", user_id="prisoner", actor_id="admin",
                required_stones=20, reason="parallel jail", now=101,
            )
    finally:
        db.close()
