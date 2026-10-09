from __future__ import annotations

import random
import unittest

from game.engine import GameEngine, GameError


class ShopDisplayTests(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(":memory:")
        self.engine.players.create("1", "Tiên A", "tien")

    def test_catalog_has_emoji_tier_and_effect(self):
        catalog = self.engine.economy.shop_catalog()
        items = [it for cat in catalog["categories"] for it in cat["items"]]
        item = next(it for it in items if it["id"] == "loi_kiep_dan")
        self.assertTrue(item["emoji"])
        self.assertEqual(item["rarity"], "Địa")
        self.assertTrue(any("Kháng lôi" in effect for effect in item["effects"]))


class PvpWagerTests(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(":memory:", rng=random.Random(3))
        self.engine.players.create("1", "Tiên A", "tien")
        self.engine.players.create("2", "Ma B", "ma")
        for uid, amount in (("1", 1000), ("2", 1000)):
            player = self.engine.players.get(uid)
            player.spirit_stones = amount
            player.attack = 100
            player.max_hp = 80
            self.engine._players.save(player)

    def test_challenge_does_not_deduct_before_accept(self):
        before = self.engine.players.get("1").spirit_stones
        challenge = self.engine.pvp.challenge("1", "2", "stones", 90, challenger_share=45)
        self.assertEqual(challenge["target_amount"], 110)
        self.assertEqual(self.engine.players.get("1").spirit_stones, before)

    def test_accept_escrows_ratio_and_winner_gets_pot(self):
        challenge = self.engine.pvp.challenge("1", "2", "stones", 90, challenger_share=45)
        match = self.engine.pvp.accept(challenge["id"], "2")
        self.assertEqual(self.engine.players.get("1").spirit_stones, 910)
        self.assertEqual(self.engine.players.get("2").spirit_stones, 890)
        # Force a near-finish state to make settlement deterministic.
        loser = match["target_id"]
        match["hp"][loser] = 1
        match["turn"] = match["challenger_id"]
        for _ in range(40):
            if match["status"] != "active":
                break
            uid = match["turn"]
            match = self.engine.pvp.act(match["id"], uid, "attack")
        self.assertEqual(match["status"], "finished")
        winner = match["winner_id"]
        self.assertEqual(self.engine.players.get(winner).spirit_stones, 1110 if winner == "1" else 1090)
        self.assertEqual(self.engine.db.fetchone("SELECT status FROM pvp_matches WHERE match_id=?", (challenge["id"],))["status"], "finished")

    def test_item_wager_refunds_on_bot_restart(self):
        self.engine._inventory.add("1", "tu_khi_dan", 3)
        self.engine._inventory.add("2", "tu_khi_dan", 3)
        challenge = self.engine.pvp.challenge("1", "2", "item", 2, item_id="tu_khi_dan")
        self.engine.pvp.accept(challenge["id"], "2")
        self.assertEqual(self.engine._inventory.get_count("1", "tu_khi_dan"), 1)
        # Constructing a new service against the same DB simulates process restart.
        from game.repositories.pvp_repository import PvpRepository
        from game.services.pvp_service import PvpService
        recovered = PvpService(self.engine._players, self.engine._inventory, self.engine.combat, PvpRepository(self.engine.db), random.Random(1))
        self.assertEqual(self.engine._inventory.get_count("1", "tu_khi_dan"), 3)
        self.assertEqual(self.engine._inventory.get_count("2", "tu_khi_dan"), 3)
        self.assertEqual(self.engine.db.fetchone("SELECT status FROM pvp_matches WHERE match_id=?", (challenge["id"],))["status"], "refunded")

    def test_invalid_ratio_rejected(self):
        with self.assertRaises(GameError):
            self.engine.pvp.challenge("1", "2", "stones", 10, challenger_share=40)
