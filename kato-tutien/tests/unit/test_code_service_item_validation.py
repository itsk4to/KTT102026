import unittest
from game.services.code_service import CodeService
from game.services.errors import GameError


class FakeRepo:
    def __init__(self): self.created = []
    def exists(self, code): return False
    def create(self, *args): self.created.append(args)

class FakeAudit:
    def log(self, *args): pass

class FakePlayers:
    pass

class CodeServiceItemValidationTests(unittest.TestCase):
    def setUp(self):
        self.repo = FakeRepo()
        self.service = CodeService(FakePlayers(), FakeAudit(), self.repo)

    def test_unknown_item_id_is_rejected_with_hint(self):
        with self.assertRaisesRegex(GameError, "vatpham"):
            self.service.create("admin", "TEST-1", 0, "not_an_item", 1, 1)
        self.assertEqual(self.repo.created, [])

    def test_valid_item_id_is_normalized_and_accepted(self):
        result = self.service.create("admin", "TEST-2", 0, " TU_KHI_DAN ", 2, 1)
        self.assertEqual(result["item"], "tu_khi_dan")
        self.assertEqual(self.repo.created[0][2], "tu_khi_dan")

    def test_quantity_without_item_is_rejected(self):
        with self.assertRaises(GameError):
            self.service.create("admin", "TEST-3", 100, None, 2, 1)

    def test_item_requires_positive_quantity(self):
        with self.assertRaises(GameError):
            self.service.create("admin", "TEST-4", 0, "tu_khi_dan", 0, 1)


if __name__ == "__main__":
    unittest.main()
