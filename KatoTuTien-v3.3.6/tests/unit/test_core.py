"""Core gameplay unit tests — no Discord."""
from __future__ import annotations

import unittest

from game.engine import GameEngine, GameError
from game.rules.combat_rules import hit_chance, calculate_damage, mastery_multiplier
from game.rules.economy_rules import seller_gain, tax_amount
from game.rules.cultivation_rules import breakthrough_chance


class PlayerTests(unittest.TestCase):
    def setUp(self):
        self.eng = GameEngine(":memory:")

    def test_create_and_info(self):
        p = self.eng.players.create("u1", "A", "tien")
        self.assertEqual(p.path, "tien")
        info = self.eng.players.info_text("u1")
        self.assertIn("realm", info)

    def test_duplicate_create(self):
        self.eng.players.create("u1", "A", "tien")
        with self.assertRaises(GameError):
            self.eng.players.create("u1", "A", "ma")


class CultivationTests(unittest.TestCase):
    def setUp(self):
        self.eng = GameEngine(":memory:")
        self.eng.players.create("u1", "A", "tien")

    def test_cultivate(self):
        r = self.eng.cultivation.cultivate("u1")
        self.assertGreater(r["gain"], 0)

    def test_cultivate_cooldown(self):
        self.eng.cultivation.cultivate("u1")
        with self.assertRaises(GameError):
            self.eng.cultivation.cultivate("u1")

    def test_breakthrough_not_ready(self):
        with self.assertRaises(GameError):
            self.eng.cultivation.breakthrough("u1")


class CombatRulesTests(unittest.TestCase):
    def test_hit_chance_bounds(self):
        self.assertGreaterEqual(hit_chance(0, 100), 0.35)
        self.assertLessEqual(hit_chance(100, 0), 0.97)

    def test_damage_positive(self):
        self.assertGreaterEqual(calculate_damage(50, 10), 1)

    def test_mastery_cap(self):
        self.assertAlmostEqual(mastery_multiplier(12), 1.12)
        self.assertAlmostEqual(mastery_multiplier(100), 1.12)


class EconomyRulesTests(unittest.TestCase):
    def test_market_tax(self):
        total = 1000
        self.assertEqual(seller_gain(total) + tax_amount(total), total)
        self.assertEqual(seller_gain(total), 980)


class CombatServiceTests(unittest.TestCase):
    def setUp(self):
        self.eng = GameEngine(":memory:")
        self.eng.players.create("u1", "A", "tien")

    def test_start_and_attack(self):
        enc = self.eng.combat.start_encounter("u1")
        self.assertFalse(enc.finished)
        r = self.eng.combat.attack("u1")
        self.assertIn("logs", r)


class SectTests(unittest.TestCase):
    def setUp(self):
        self.eng = GameEngine(":memory:")
        self.eng.players.create("owner", "Owner", "tien")
        p = self.eng.players.get("owner")
        p.spirit_stones = 50_000
        self.eng._players.save(p)

    def test_create_sect(self):
        r = self.eng.sect.create("owner", "Thiên Kiếm Môn")
        self.assertEqual(r["sect"].name, "Thiên Kiếm Môn")
        ov = self.eng.sect.overview("owner")
        self.assertTrue(ov["in_sect"])


class MarketTests(unittest.TestCase):
    def setUp(self):
        self.eng = GameEngine(":memory:")
        self.eng.players.create("s", "Seller", "tien")
        self.eng.players.create("b", "Buyer", "ma")
        for uid in ("s", "b"):
            p = self.eng.players.get(uid)
            p.spirit_stones = 100_000
            self.eng._players.save(p)
        self.eng.economy.buy("s", "tu_khi_dan", 3)

    def test_list_and_buy(self):
        listed = self.eng.economy.market_list("s", "tu_khi_dan", 2, 5000)
        lid = listed["listing_id"]
        r = self.eng.economy.market_buy("b", lid)
        self.assertEqual(r["tax"], 100)  # 2% of 5000
        self.assertEqual(r["seller_gain"], 4900)


class ExplorationChoiceTests(unittest.TestCase):
    def setUp(self):
        import random
        self.eng = GameEngine(":memory:", rng=random.Random(1))
        self.eng.players.create("u1", "A", "tien")
        p = self.eng.players.get("u1")
        p.last_explore = 0
        p.mind = 100
        p.insight = 100
        self.eng._players.save(p)

    def test_choice_event_can_be_resolved_and_persisted(self):
        # Force the narrative branch without relying on global randomness.
        service = self.eng.exploration
        event = {
            "key": "test_event", "title": "Thử thách", "weight": 1,
            "text": "Một cánh cửa cổ xuất hiện.",
            "choices": [{"id": "open", "label": "Mở", "effect": {"cultivation": [10, 10], "discover": "test_discovery", "text": "Cửa mở."}}]
        }
        service._save_pending("u1", event, "hoangnguyen")
        pending = service.explore("u1")
        self.assertTrue(pending["choice"])
        result = service.choose("u1", "open")
        self.assertEqual(result["cultivation"], 10)
        self.assertIsNone(service.pending("u1"))
        self.assertTrue(self.eng._players.has_discovery("u1", "test_discovery"))


if __name__ == "__main__":
    unittest.main()
