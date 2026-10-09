from __future__ import annotations
import random
from game.database.connection import Database
from game.database.schema import SCHEMA_VERSION
from game.engine import GameEngine, GameError
from game.content.sects_content import SECT_MISSIONS
import pytest


def make_engine(tmp_path):
    return GameEngine(Database(str(tmp_path / "test.db")), random.Random(7))


def test_schema_and_dao_lu(tmp_path):
    engine = make_engine(tmp_path)
    assert SCHEMA_VERSION == 14
    a = engine.players.create("a", "A", "tien")
    engine.players.create("b", "B", "tien")
    engine.dao_lu.request("a", "b")
    engine.dao_lu.accept("b", "a")
    assert engine.dao_lu.song_tu("a")["intimacy"] == 1


def test_sect_expansion(tmp_path):
    engine = make_engine(tmp_path)
    p = engine.players.create("a", "A", "tien")
    p.spirit_stones = 20000
    engine._players.save(p)
    sect = engine.sect.create("a", "Test Sect")["sect"]
    sect = engine._sects.get(sect.sect_id)
    sect.treasury = 20000
    engine._sects.save(sect)
    assert "chance" in engine.sect_tower.challenge("a")
    assert engine.sect_tower.upgrade_lingmai("a")["level"] == 1
    state = engine.sect_tower.mission_state("a")
    for _ in range(state["mission"]["target"]):
        engine.sect_tower.record_activity("a", next(k for k,v in SECT_MISSIONS.items() if v == state["mission"]), 1)
    assert "progress" in engine.sect_tower.claim_mission("a")
    with pytest.raises(GameError):
        engine.sect_tower.claim_mission("a")


def test_dynamic_redeem_code(tmp_path):
    engine = make_engine(tmp_path)
    engine.players.create("a", "A", "tien")
    engine.codes.create("admin", "TEST-V338", 123, "tu_khi_dan", 2, 2)
    result = engine.economy.redeem_code("a", "TEST-V338")
    assert result["stones"] == 123
    assert result["qty"] == 2


def test_dynamic_redeem_code_can_be_disabled(tmp_path):
    engine = make_engine(tmp_path)
    engine.players.create("a", "A", "tien")
    engine.players.create("b", "B", "tien")
    engine.codes.create("admin", "DISABLE-ME", 123, None, 0, 5)
    assert engine.codes.disable("admin", "DISABLE-ME")["code"] == "DISABLE-ME"
    with pytest.raises(GameError, match="vô hiệu hóa"):
        engine.economy.redeem_code("a", "DISABLE-ME")
    with pytest.raises(GameError, match="vô hiệu hóa"):
        engine.codes.disable("admin", "DISABLE-ME")


def test_dao_choice_and_dao_lu_reject(tmp_path):
    engine = make_engine(tmp_path)
    engine.players.create("a", "A", "tien")
    engine.players.create("b", "B", "tien")
    assert engine.dao.choose("a", "kiem")["dao"]["name"] == "Kiếm Đạo"
    engine.dao_lu.request("a", "b")
    engine.dao_lu.reject("b", "a")
    assert engine.dao_lu.pending("b") == []
