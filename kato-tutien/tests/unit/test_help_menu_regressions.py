from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[2]


class HelpMenuRegressionTests(unittest.TestCase):
    def test_core_and_help_view_parse(self):
        for relative in ("ui/commands/core.py", "ui/views/help_view.py", "ui/views/main_menu_view.py"):
            ast.parse((ROOT / relative).read_text(encoding="utf-8"))

    def test_help_uses_real_newlines_and_pagination(self):
        source = (ROOT / "ui/commands/core.py").read_text(encoding="utf-8")
        self.assertIn('"\\n".join(lines)', source)
        self.assertNotIn('"\\\\n".join(lines)', source)
        self.assertIn("HelpView(pages", source)

    def test_menu_opens_dashboard_not_help(self):
        source = (ROOT / "ui/commands/core.py").read_text(encoding="utf-8")
        start = source.index("async def cmd_menu(")
        end = source.index("async def cmd_help(", start)
        menu_handler = source[start:end]
        self.assertIn("build_main_embed", menu_handler)
        self.assertIn("MainMenuView", menu_handler)
        self.assertNotIn("await cmd_help", menu_handler)

    def test_market_is_available_in_select_menu(self):
        source = (ROOT / "ui/views/main_menu_view.py").read_text(encoding="utf-8")
        self.assertIn('SelectOption(label="Chợ", value="market"', source)


if __name__ == "__main__":
    unittest.main()
