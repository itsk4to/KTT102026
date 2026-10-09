from collections import Counter
import unittest

from game.content.items import ITEMS, SHOP_CATEGORIES, SHOP_ORDER


class ItemBalanceTests(unittest.TestCase):
    def test_each_shop_category_has_at_most_ten_items(self):
        counts = Counter(item["category"] for item in ITEMS.values())
        for category in SHOP_ORDER:
            self.assertLessEqual(counts[category], 10, category)
            self.assertEqual(len(SHOP_CATEGORIES[category]), counts[category])
        self.assertEqual({k: counts[k] for k in SHOP_ORDER}, {
            "Đan dược": 10, "Bùa chú": 10, "Pháp bảo": 10,
            "Binh khí": 10, "Công pháp": 10,
        })

    def test_equipment_stats_are_bounded(self):
        for item_id, item in ITEMS.items():
            if item.get("type") != "equipment":
                continue
            self.assertLessEqual(item.get("attack", 0), 45, item_id)
            self.assertLessEqual(item.get("defense", 0), 35, item_id)
            self.assertLessEqual(item.get("max_hp", 0), 25, item_id)
            self.assertLessEqual(item.get("thunder_resistance", 0), 0.10, item_id)

    def test_consumable_permanent_bonuses_are_small(self):
        for item_id, item in ITEMS.items():
            if item.get("type") != "consumable":
                continue
            for stat in ("root", "insight", "luck", "fate", "mind", "all_stats"):
                self.assertLessEqual(item.get(stat, 0), 2, (item_id, stat))
            self.assertLessEqual(item.get("breakthrough_bonus", 0), 0.08, item_id)
            self.assertLessEqual(item.get("thunder_resistance", 0), 0.12, item_id)

    def test_technique_multipliers_are_bounded(self):
        for item_id, item in ITEMS.items():
            if item.get("type") == "technique":
                self.assertLessEqual(item.get("skill_power", 1.0), 1.25, item_id)
                self.assertLessEqual(item.get("technique_bonus", 0), 2, item_id)
                self.assertIn(item.get("technique_stat"), {"root", "insight", "luck", "fate", "mind"})


if __name__ == "__main__":
    unittest.main()
