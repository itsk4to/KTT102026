"""Shop service tests — required by v3 blueprint."""
from __future__ import annotations

import unittest

from game.engine import GameEngine, GameError


class ShopTests(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(":memory:")
        self.engine.players.create("1", "Tester", "tien")
        # grant stones
        p = self.engine.players.get("1")
        p.spirit_stones = 1_000_000
        self.engine._players.save(p)

    def test_shop_loads(self):
        catalog = self.engine.economy.shop_catalog()
        self.assertIn("categories", catalog)
        self.assertTrue(len(catalog["categories"]) > 0)

    def test_shop_category_loads(self):
        catalog = self.engine.economy.shop_catalog()
        names = [c["name"] for c in catalog["categories"]]
        self.assertIn("Đan dược", names)

    def test_buy_valid_item(self):
        r = self.engine.economy.buy("1", "tu_khi_dan", 2)
        self.assertEqual(r["qty"], 2)
        self.assertEqual(self.engine.economy.inventory("1")[0]["id"], "tu_khi_dan")

    def test_buy_insufficient_funds(self):
        p = self.engine.players.get("1")
        p.spirit_stones = 10
        self.engine._players.save(p)
        with self.assertRaises(GameError):
            self.engine.economy.buy("1", "hon_don_dao_kinh", 1)

    def test_buy_invalid_item(self):
        with self.assertRaises(GameError):
            self.engine.economy.buy("1", "not_exist", 1)

    def test_buy_quantity(self):
        r = self.engine.economy.buy("1", "tu_khi_dan", 5)
        self.assertEqual(r["qty"], 5)
        inv = {i["id"]: i["qty"] for i in self.engine.economy.inventory("1")}
        self.assertEqual(inv["tu_khi_dan"], 5)

    def test_inventory_receives_item(self):
        self.engine.economy.buy("1", "hoi_khi_dan", 1)
        ids = [i["id"] for i in self.engine.economy.inventory("1")]
        self.assertIn("hoi_khi_dan", ids)

    def test_transaction_deducts_stones(self):
        before = self.engine.players.get("1").spirit_stones
        r = self.engine.economy.buy("1", "tu_khi_dan", 1)
        after = self.engine.players.get("1").spirit_stones
        self.assertEqual(before - after, r["total"])


if __name__ == "__main__":
    unittest.main()
