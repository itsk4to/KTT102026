from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from game.database.connection import Database
from game.engine import GameEngine, GameError
from game.rules.cultivation_rules import cultivation_requirement
from game.services.player_mission_service import PlayerMissionService
from game.content.recurring_missions import MISSIONS

VN = ZoneInfo("Asia/Ho_Chi_Minh")


class FixedRng:
    def __init__(self, roll: float):
        self.roll = roll

    def random(self):
        return self.roll


def make_engine():
    engine = GameEngine(Database(":memory:"))
    player = engine.players.create("u1", "Tester", "tien")
    return engine, player


def test_failed_breakthrough_adds_five_pity_points_and_persists():
    engine, player = make_engine()
    player.realm_index = 1
    player.realm_layer = 1
    player.cultivation = cultivation_requirement(player.realm_index, player.realm_layer)
    engine._players.save(player)
    engine.cultivation.rng = FixedRng(0.99)

    result = engine.cultivation.breakthrough("u1")

    assert result["success"] is False
    assert result["pity_before"] == 0
    assert result["pity_after"] == 5
    assert engine.players.get("u1").breakthrough_pity == 5
    assert engine.cultivation.breakthrough_preview("u1")["pity_bonus"] == 0.05


def test_pity_caps_at_twenty_percentage_points():
    engine, player = make_engine()
    player.realm_index = 1
    player.realm_layer = 1
    player.cultivation = cultivation_requirement(player.realm_index, player.realm_layer)
    player.breakthrough_pity = 20
    engine._players.save(player)
    engine.cultivation.rng = FixedRng(0.99)

    result = engine.cultivation.breakthrough("u1")

    assert result["pity_after"] == 20
    assert engine.players.get("u1").breakthrough_pity == 20


def test_breakthrough_success_resets_pity():
    engine, player = make_engine()
    player.realm_index = 1
    player.realm_layer = 1
    player.cultivation = cultivation_requirement(player.realm_index, player.realm_layer)
    player.breakthrough_pity = 15
    engine._players.save(player)
    engine.cultivation.rng = FixedRng(0.0)

    result = engine.cultivation.breakthrough("u1")

    assert result["success"] is True
    assert result["pity_after"] == 0
    assert engine.players.get("u1").breakthrough_pity == 0


def test_failed_tribulation_also_adds_pity():
    engine, player = make_engine()
    from game.content.realms import REALMS, TRIBULATION_REALM_INDEX
    player.realm_index = TRIBULATION_REALM_INDEX
    player.realm_layer = REALMS[TRIBULATION_REALM_INDEX][1]
    player.cultivation = cultivation_requirement(player.realm_index, player.realm_layer)
    engine._players.save(player)
    engine.cultivation.rng = FixedRng(0.99)

    result = engine.cultivation.face_tribulation("u1")

    assert result["success"] is False
    assert result["pity_after"] == 5


def test_mission_progress_claims_once_and_pays_bounded_rewards():
    engine, player = make_engine()
    initial_stones = player.spirit_stones
    engine.missions.track_action("u1", "cultivate", 1)

    mission = next(x for x in engine.missions.list_missions("u1") if x["id"] == "starter_cultivate")
    assert mission["claimable"] is True
    claim = engine.missions.claim("u1", "starter_cultivate")
    assert claim["stones"] == 300
    assert claim["cultivation"] <= claim["cultivation_requested"]
    assert engine.players.get("u1").spirit_stones == initial_stones + 300
    with pytest.raises(GameError, match="đã được nhận"):
        engine.missions.claim("u1", "starter_cultivate")


def test_successful_purchase_advances_purchase_missions():
    engine, _ = make_engine()
    engine.economy.buy("u1", "tu_khi_dan", 1)
    missions = {x["id"]: x for x in engine.missions.list_missions("u1")}
    assert missions["starter_purchase"]["progress"] == 1
    assert missions["daily_purchase"]["progress"] == 1
    assert missions["weekly_purchase"]["progress"] == 1


def test_failed_purchase_does_not_advance_missions():
    engine, player = make_engine()
    player.spirit_stones = 0
    engine._players.save(player)
    with pytest.raises(GameError):
        engine.economy.buy("u1", "tu_khi_dan", 1)
    missions = {x["id"]: x for x in engine.missions.list_missions("u1")}
    assert missions["starter_purchase"]["progress"] == 0


def test_daily_and_weekly_period_keys_use_vietnam_time():
    daily_one = datetime(2026, 10, 10, 23, 59, tzinfo=VN)
    daily_two = datetime(2026, 10, 11, 0, 1, tzinfo=VN)
    weekly_one = datetime(2026, 10, 11, 23, 59, tzinfo=VN)
    weekly_two = datetime(2026, 10, 12, 0, 1, tzinfo=VN)
    daily = next(v for v in MISSIONS.values() if v["group"] == "daily")
    weekly = next(v for v in MISSIONS.values() if v["group"] == "weekly")
    assert PlayerMissionService.period_key(daily, daily_one) != PlayerMissionService.period_key(daily, daily_two)
    assert PlayerMissionService.period_key(weekly, weekly_one) != PlayerMissionService.period_key(weekly, weekly_two)


def test_successful_cultivation_advances_missions_automatically():
    engine, _ = make_engine()
    engine.cultivation.cultivate("u1")
    missions = {x["id"]: x for x in engine.missions.list_missions("u1")}
    assert missions["starter_cultivate"]["progress"] == 1
    assert missions["daily_cultivate"]["progress"] == 1
    assert missions["weekly_cultivate"]["progress"] == 1


def test_successful_exploration_advances_missions_automatically():
    engine, _ = make_engine()
    engine.exploration.explore("u1")
    missions = {x["id"]: x for x in engine.missions.list_missions("u1")}
    assert missions["starter_explore"]["progress"] == 1
    assert missions["daily_explore"]["progress"] == 1
    assert missions["weekly_explore"]["progress"] == 1


def test_schema_v16_migration_keeps_existing_player_data():
    from game.database.migrations import run_migrations
    from game.database.schema import SCHEMA_VERSION

    engine, player = make_engine()
    player.spirit_stones = 4321
    engine._players.save(player)
    engine.db.execute("UPDATE schema_meta SET value='15' WHERE key='version'")

    assert run_migrations(engine.db) == 16
    loaded = engine.players.get("u1")
    assert loaded.spirit_stones == 4321
    assert loaded.breakthrough_pity == 0
    assert SCHEMA_VERSION == 16
    assert engine.db.fetchone("SELECT 1 FROM player_mission_progress LIMIT 1") is None
