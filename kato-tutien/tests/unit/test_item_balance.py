from collections import Counter
import unittest

from game.content.items import ITEMS, SHOP_CATEGORIES, SHOP_ORDER, ITEM_ROLES


class ItemBalanceTests(unittest.TestCase):
    def test_shop_categories_are_populated_and_consistent(self):
        counts = Counter(item["category"] for item in ITEMS.values() if item.get("price"))
        for category in SHOP_ORDER:
            self.assertGreaterEqual(counts[category], 1, category)
            self.assertEqual(len(SHOP_CATEGORIES[category]), counts[category])
            # Soft ceiling — enough variety, not an unmaintainable dump.
            self.assertLessEqual(counts[category], 16, category)

    def test_every_item_has_a_known_role(self):
        for item_id, item in ITEMS.items():
            role = item.get("role")
            self.assertIn(role, ITEM_ROLES, item_id)

    def test_equipment_stats_are_bounded(self):
        for item_id, item in ITEMS.items():
            if item.get("type") != "equipment":
                continue
            self.assertLessEqual(item.get("attack", 0), 50, item_id)
            self.assertLessEqual(item.get("defense", 0), 40, item_id)
            self.assertLessEqual(item.get("max_hp", 0), 40, item_id)
            self.assertLessEqual(item.get("thunder_resistance", 0), 0.12, item_id)

    def test_consumable_permanent_bonuses_are_small(self):
        for item_id, item in ITEMS.items():
            if item.get("type") != "consumable":
                continue
            for stat in ("root", "insight", "luck", "fate", "mind", "all_stats"):
                self.assertLessEqual(item.get(stat, 0), 3, (item_id, stat))
            self.assertLessEqual(item.get("breakthrough_bonus", 0), 0.12, item_id)
            self.assertLessEqual(item.get("thunder_resistance", 0), 0.15, item_id)
            # Single primary combat-stat purpose for foundation/thunder items
            if item.get("role") == "breakthrough":
                self.assertTrue(item.get("breakthrough_bonus", 0) > 0, item_id)
                self.assertFalse(item.get("cultivation"), item_id)
            if item.get("role") == "thunder_guard" and item.get("type") == "consumable":
                self.assertTrue(item.get("thunder_resistance", 0) > 0, item_id)

    def test_technique_multipliers_are_bounded(self):
        for item_id, item in ITEMS.items():
            if item.get("type") == "technique":
                self.assertLessEqual(item.get("skill_power", 1.0), 1.35, item_id)
                self.assertLessEqual(item.get("technique_bonus", 0), 3, item_id)
                self.assertIn(item.get("technique_stat"), {"root", "insight", "luck", "fate", "mind"})


if __name__ == "__main__":
    unittest.main()
