import unittest

from game.database.schema import SCHEMA_VERSION
from game.version import version_status


class VersionTests(unittest.TestCase):
    def test_version_sources_are_consistent(self):
        data = version_status()
        self.assertTrue(data["consistent"])
        self.assertEqual(data["version"], data["pyproject_version"])
        self.assertTrue(str(SCHEMA_VERSION).isdigit())


if __name__ == "__main__":
    unittest.main()
