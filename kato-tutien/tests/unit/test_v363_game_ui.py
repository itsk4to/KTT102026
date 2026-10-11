from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[2]


class GameUIReworkTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_version_is_363_everywhere_current(self):
        self.assertEqual(self.read("VERSION.txt").strip(), "3.6.3")
        self.assertIn('version = "3.6.3"', self.read("pyproject.toml"))

    def test_theme_factory_has_shared_brand_and_semantic_colors(self):
        tokens = self.read("ui/theme/tokens.py")
        embeds = self.read("ui/theme/embeds.py")
        views = self.read("ui/theme/views.py")
        self.assertIn("BRAND_FOOTER", tokens)
        self.assertIn("color_for_title", embeds)
        self.assertIn("class ThemedView(discord.ui.View)", views)
        self.assertIn("BUTTON_EMOJIS", views)

    def test_main_menu_is_compact_select_plus_quick_actions(self):
        source = self.read("ui/views/main_menu_view.py")
        self.assertIn("self.add_item(MainMenuSelect(self))", source)
        self.assertIn('("Nhân vật", "player", "cultivator")', source)
        self.assertIn('("Khám phá", "explore", "explore")', source)
        self.assertIn('"Làm mới"', source)
        self.assertIn('"Đóng menu"', source)
        self.assertIn('SelectOption(label="Chợ", value="market"', source)

    def test_player_menu_has_action_select(self):
        source = self.read("ui/views/player_view.py")
        self.assertIn("class PlayerActionSelect(discord.ui.Select)", source)
        self.assertIn("self.add_item(PlayerActionSelect(self))", source)
        self.assertIn("progress_bar(current, requirement, 12)", source)

    def test_shop_is_a_category_to_item_to_detail_flow(self):
        source = self.read("ui/views/shop_view.py")
        self.assertIn("class ShopCategorySelect", source)
        self.assertIn("class ShopItemSelect", source)
        self.assertIn("✨ Hiệu ứng / chỉ số", source)
        self.assertIn("Mã vật phẩm", source)

    def test_inventory_and_mission_use_mobile_friendly_panels(self):
        inventory = self.read("ui/views/inventory_view.py")
        missions = self.read("ui/views/mission_view.py")
        self.assertIn("_PAGE_SIZE = 12", inventory)
        self.assertIn("NHIỆM VỤ KHỞI HÀNH", missions)
        self.assertIn("NHIỆM VỤ HẰNG NGÀY", missions)
        self.assertIn("NHIỆM VỤ HẰNG TUẦN", missions)

    def test_dao_selection_uses_dropdown_then_confirmation(self):
        source = self.read("ui/views/dao_view.py")
        self.assertIn("class DaoPathSelect(discord.ui.Select)", source)
        self.assertIn("Chọn Đạo", source)
        self.assertIn("_choose_selected", source)

    def test_exploration_and_world_use_stat_fields_and_progress(self):
        exploration = self.read("ui/views/exploration_view.py")
        world = self.read("ui/views/world_view.py")
        self.assertIn("Dấu vết yêu thú", exploration)
        self.assertIn("Dị tượng / Boss", exploration)
        self.assertIn("progress", world)
        self.assertIn("Chọn một biến động", world)

    def test_ui_python_sources_parse(self):
        targets = [
            "ui/theme/tokens.py", "ui/theme/embeds.py", "ui/theme/components.py", "ui/theme/views.py",
            "ui/embeds.py", "ui/views/main_menu_view.py", "ui/views/player_view.py",
            "ui/views/shop_view.py", "ui/views/inventory_view.py", "ui/views/mission_view.py",
            "ui/views/secret_realm_view.py", "ui/views/exploration_view.py", "ui/views/market_view.py",
            "ui/views/world_view.py", "ui/views/dao_view.py", "ui/views/combat_view.py",
        ]
        for relative in targets:
            with self.subTest(file=relative):
                ast.parse(self.read(relative), filename=relative)


if __name__ == "__main__":
    unittest.main()
