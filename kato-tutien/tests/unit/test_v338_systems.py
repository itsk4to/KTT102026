from __future__ import annotations
import random
from game.database.connection import Database
from game.database.schema import SCHEMA_VERSION
from game.engine import GameEngine


def make_engine(tmp_path):
    return GameEngine(Database(str(tmp_path / "test.db")), random.Random(7))


def test_schema_and_dao_lu(tmp_path):
    engine = make_engine(tmp_path)
    assert SCHEMA_VERSION == 8
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
    assert "progress" in engine.sect_tower.claim_mission("a")


def test_dynamic_redeem_code(tmp_path):
    engine = make_engine(tmp_path)
    engine.players.create("a", "A", "tien")
    engine.codes.create("admin", "TEST-V338", 123, "tu_khi_dan", 2, 2)
    result = engine.economy.redeem_code("a", "TEST-V338")
    assert result["stones"] == 123
    assert result["qty"] == 2
