from __future__ import annotations

import time

import pytest

from game.database.connection import Database
from game.engine import GameEngine, GameError
from game.rules.breakthrough_rules import breakthrough_recovery_seconds


def test_failed_breakthrough_locks_cultivation_by_realm():
    eng = GameEngine(Database(":memory:"))
    eng.players.create("u", "U", "tien")
    p = eng.players.get("u")
    p.realm_index = 2
    p.realm_layer = 1
    p.cultivation = 10000
    eng._players.save(p)

    class FixedRng:
        def random(self):
            return 0.99

    eng.cultivation.rng = FixedRng()
    result = eng.cultivation.breakthrough("u")
    assert result["success"] is False
    assert result["recovery_seconds"] == 120

    with pytest.raises(GameError, match="hồi phục"):
        eng.cultivation.cultivate("u")
    with pytest.raises(GameError, match="hồi phục"):
        eng.cultivation.breakthrough("u")


def test_recovery_lock_expires():
    eng = GameEngine(Database(":memory:"))
    eng.players.create("u", "U", "tien")
    p = eng.players.get("u")
    p.breakthrough_recovery_until = int(time.time()) - 1
    p.cultivation = 0
    eng._players.save(p)
    result = eng.cultivation.breakthrough_preview("u")
    assert result["recovery_remaining"] == 0


def test_recovery_milestones_scale_with_realm():
    assert breakthrough_recovery_seconds(1, 1) == 60
    assert breakthrough_recovery_seconds(2, 1) == 120
    assert breakthrough_recovery_seconds(8, 9) == 4500
    assert breakthrough_recovery_seconds(9, 3, tribulation=True) == 10800
