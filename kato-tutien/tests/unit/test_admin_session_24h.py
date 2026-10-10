from __future__ import annotations

import time

from game.database.connection import Database
from game.engine import GameEngine
from game.security.admin_auth import AdminAuth
from config import ADMIN_SESSION_TTL


def test_admin_session_expires_after_one_day_and_persists_across_restart(tmp_path):
    db_path = tmp_path / "admin-session.db"
    engine = GameEngine(str(db_path))

    expires_at = engine.admin_auth.grant("admin-1")
    now = int(time.time())
    assert ADMIN_SESSION_TTL == 24 * 60 * 60
    assert now + ADMIN_SESSION_TTL - 1 <= expires_at <= now + ADMIN_SESSION_TTL + 1
    assert engine.admin_auth.has_session("admin-1") is True
    engine.db.close()

    restarted = GameEngine(str(db_path))
    assert restarted.admin_auth.has_session("admin-1") is True
    restarted.db.close()


def test_expired_admin_session_is_rejected_and_removed():
    db = Database(":memory:")
    engine = GameEngine(db)
    engine.admin_auth.grant("admin-2")
    db.execute(
        "UPDATE admin_sessions SET expires_at=? WHERE user_id=?",
        (int(time.time()) - 1, "admin-2"),
    )

    assert engine.admin_auth.has_session("admin-2") is False
    assert db.fetchone("SELECT user_id FROM admin_sessions WHERE user_id=?", ("admin-2",)) is None


def test_clear_revokes_persisted_session():
    engine = GameEngine(Database(":memory:"))
    engine.admin_auth.grant("admin-3")
    engine.admin_auth.clear("admin-3")
    assert engine.admin_auth.has_session("admin-3") is False


def test_password_verification_uses_configured_secret_and_constant_time_compare():
    auth = AdminAuth(password="test-only-new-secret")
    assert auth.verify_password("test-only-new-secret") is True
    assert auth.verify_password("old-secret") is False
    assert AdminAuth(password="").verify_password("anything") is False
