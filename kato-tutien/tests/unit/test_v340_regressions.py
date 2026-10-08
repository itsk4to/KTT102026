from __future__ import annotations

import random

import pytest

from game.database.connection import Database
from game.engine import GameEngine, GameError
from game.content.realms import cultivation_requirement
from game.content.sects_content import SECT_MISSIONS


def make_engine():
    return GameEngine(Database(":memory:"), random.Random(11))


def test_sect_mission_is_real_progress_and_single_claim():
    eng = make_engine()
    eng.players.create("u", "U", "tien")
    p = eng.players.get("u")
    p.spirit_stones = 20_000
    eng._players.save(p)
    eng.sect.create("u", "Thiên Môn")
    state = eng.sect_tower.mission_state("u")
    key = next(k for k, v in SECT_MISSIONS.items() if v == state["mission"])
    target = state["mission"]["target"]
    eng.sect_tower.record_activity("u", key, target)
    claim = eng.sect_tower.claim_mission("u")
    assert claim["claimed"] is True
    with pytest.raises(GameError):
        eng.sect_tower.claim_mission("u")


def test_breakthrough_preview_never_consumes_item_and_failure_rolls_back_consume():
    eng = make_engine()
    eng.players.create("u", "U", "tien")
    eng._inventory.add("u", "tru_co_dan", 1)
    before = eng._inventory.get_count("u", "tru_co_dan")
    preview = eng.breakthrough.preview_item("u", "tru_co_dan")
    assert preview["bonus"] > 0
    assert eng._inventory.get_count("u", "tru_co_dan") == before

    original = eng.cultivation.breakthrough
    def fail(*_args, **_kwargs):
        raise RuntimeError("forced rollback")
    eng.cultivation.breakthrough = fail
    with pytest.raises(RuntimeError):
        eng.breakthrough.breakthrough("u", item_id="tru_co_dan")
    eng.cultivation.breakthrough = original
    assert eng._inventory.get_count("u", "tru_co_dan") == before


def test_dao_progress_and_combat_stats_use_dao_and_talent():
    eng = make_engine()
    p = eng.players.create("u", "U", "tien")
    eng.dao.choose("u", "kiem")
    p = eng.players.get("u")
    assert p.dao_type == "kiem"
    old_insight = p.dao_insight
    eng.cultivation.cultivate("u")
    p = eng.players.get("u")
    assert p.dao_insight == old_insight + 1
    p.dao_stage = 2
    p.dao_insight = 40
    p.talent = "Sát Phạt"
    eng._players.save(p)
    stats = eng.combat.battle_stats(eng.players.get("u"))
    assert stats["crit"] > 0.05
    assert stats["spirit_mult"] >= 1.0


def test_reputation_and_world_event_zone_are_real():
    eng = make_engine()
    eng.players.create("u", "U", "tien")
    p = eng.players.get("u")
    assert p.reputation == 0
    eng.exploration._apply_effect(p, "u", {"reputation": 3}, {})
    eng._players.save(p)
    assert eng.players.get("u").reputation == 3

    eng.world.world.create("hon_hac_long", "yeuthusonmach", 1, 9999999999)
    with pytest.raises(GameError):
        eng.world.contribute("u", "hon_hac_long")
    p = eng.players.get("u")
    p.explore_zone = "yeuthusonmach"
    eng._players.save(p)
    assert eng.world.contribute("u", "hon_hac_long")["finished"] is True


def test_market_price_is_explicitly_per_unit():
    eng = make_engine()
    eng.players.create("seller", "Seller", "tien")
    eng.players.create("buyer", "Buyer", "tien")
    seller = eng.players.get("seller")
    seller.spirit_stones = 5_000
    eng._players.save(seller)
    eng.economy.buy("seller", "tu_khi_dan", 2)
    listing = eng.economy.market_list("seller", "tu_khi_dan", 2, 500)
    row = eng._market.get(listing["listing_id"])
    assert row.price == 1000
    assert row.unit_price == 500
    assert eng.economy.market_browse(1)[0]["price_each"] == 500


def test_npc_and_talent_rules_are_not_decorative():
    eng = make_engine()
    eng.players.create("u", "U", "tien")
    p = eng.players.get("u")
    p.talent = "Thanh Tâm"
    p.explore_zone = "hoangnguyen"
    p.realm_index = 5
    eng._players.save(p)
    with pytest.raises(GameError):
        eng.npc.talk("u", "co_nu")

    # The talent modifier must feed the canonical breakthrough injury rule.
    rolled = __import__('game.rules.breakthrough_rules', fromlist=['apply_failure_injury']).apply_failure_injury(10, 5, 0.9)
    assert rolled == 14
