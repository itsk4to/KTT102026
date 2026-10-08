from __future__ import annotations

import os
import tempfile
import unittest

from game.database.connection import Database
from game.database.migrations import run_migrations
from game.engine import GameEngine, GameError
from game.rules.sect_rules import can_change_role


class MigrationSafetyTests(unittest.TestCase):
    def test_old_player_table_gets_repaired(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            db = Database(path)
            db.execute("CREATE TABLE schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.execute("CREATE TABLE players (user_id TEXT PRIMARY KEY)")
            db.execute("INSERT INTO schema_meta(key, value) VALUES('version', '3')")
            run_migrations(db)
            columns = {row["name"] for row in db.fetchall("PRAGMA table_info(players)")}
            self.assertIn("spirit_stones", columns)
            self.assertIn("realm_index", columns)
            version = db.fetchone("SELECT value FROM schema_meta WHERE key='version'")
            self.assertEqual(version["value"], "10")
            db.close()
        finally:
            os.unlink(path)


class EconomyAtomicityTests(unittest.TestCase):
    def test_shop_rolls_back_on_inventory_failure(self):
        engine = GameEngine(":memory:")
        engine.players.create("u1", "Tester", "tien")
        p = engine.players.get("u1")
        p.spirit_stones = 1_000_000
        engine._players.save(p)
        before = engine.players.get("u1").spirit_stones

        original_add = engine.economy._inventory.add

        def broken_add(*_args, **_kwargs):
            raise RuntimeError("simulated inventory failure")

        engine.economy._inventory.add = broken_add
        try:
            with self.assertRaises(RuntimeError):
                engine.economy.buy("u1", "tu_khi_dan", 1)
        finally:
            engine.economy._inventory.add = original_add

        after = engine.players.get("u1").spirit_stones
        self.assertEqual(before, after)
        self.assertEqual(engine.economy.inventory("u1"), [])


class SectAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(":memory:")
        for uid, name in (("owner", "Owner"), ("a", "A"), ("b", "B")):
            self.engine.players.create(uid, name, "tien")
        owner = self.engine.players.get("owner")
        owner.spirit_stones = 50_000
        self.engine._players.save(owner)
        self.engine.sect.create("owner", "Thiên Kiếm Môn")

        self.engine.sect.invite("owner", "a")
        self.engine.sect.invite("owner", "b")
        self.engine.sect.accept_invite("a", 1)
        self.engine.sect.accept_invite("b", 2)

    def test_owner_can_promote_lower_member(self):
        result = self.engine.sect.change_role("owner", "a", "Trưởng Lão")
        self.assertEqual(result["role"], "Trưởng Lão")

    def test_officer_cannot_promote_to_own_or_higher_rank(self):
        self.engine.sect.change_role("owner", "a", "Phó Tông Chủ")
        with self.assertRaises(GameError):
            self.engine.sect.change_role("a", "b", "Phó Tông Chủ")

    def test_role_history_is_recorded(self):
        self.engine.sect.change_role("owner", "a", "Trưởng Lão")
        history = self.engine.sect.overview("owner")["role_history"]
        self.assertTrue(any(row["new_role"] == "Trưởng Lão" for row in history))


class SectRuleUnitTests(unittest.TestCase):
    def test_authority_matrix(self):
        self.assertTrue(can_change_role("Tông Chủ", "Ngoại Môn Đệ Tử", "Chấp Sự", promote=True))
        self.assertFalse(can_change_role("Phó Tông Chủ", "Ngoại Môn Đệ Tử", "Phó Tông Chủ", promote=True))
        self.assertTrue(can_change_role("Phó Tông Chủ", "Trưởng Lão", "Chấp Sự", promote=False))


if __name__ == "__main__":
    unittest.main()
