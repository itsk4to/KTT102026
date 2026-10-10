import unittest
from game.content.items import ITEMS
from game.content.item_catalog import search_items, category_items


class ItemCatalogLookupTests(unittest.TestCase):
    def test_search_by_exact_id(self):
        results = search_items("tu_khi_dan")
        self.assertTrue(results)
        self.assertEqual(results[0][0], "tu_khi_dan")

    def test_search_vietnamese_name_without_diacritics(self):
        results = search_items("tu khi dan")
        self.assertTrue(any(item_id == "tu_khi_dan" for item_id, _ in results))

    def test_search_by_category(self):
        results = search_items("binh khi", limit=20)
        self.assertTrue(results)
        self.assertTrue(all(item.get("category") == "Binh khí" for _, item in results))

    def test_category_browser_lists_all_items(self):
        for category in ("Đan dược", "Bùa chú", "Pháp bảo", "Binh khí", "Công pháp"):
            rows = category_items(category)
            self.assertEqual(len(rows), 10)
            self.assertTrue(all(item_id in ITEMS for item_id, _ in rows))

    def test_empty_search_is_bounded(self):
        self.assertEqual(len(search_items("", limit=7)), 7)


if __name__ == "__main__":
    unittest.main()
