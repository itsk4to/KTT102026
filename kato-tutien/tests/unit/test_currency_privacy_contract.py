from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class CurrencyPrivacyContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_currency_is_opt_in_for_player_embed(self):
        embeds = self.read("ui/embeds.py")
        self.assertIn("show_currency: bool = False", embeds)
        self.assertIn("if show_currency:", embeds)
        self.assertIn("fmt_amount(p.spirit_stones)", embeds)

    def test_only_self_info_commands_opt_in_to_show_balance(self):
        core = self.read("ui/commands/core.py")
        bot = self.read("bot.py")
        self.assertIn("show_currency=True", core)
        self.assertIn("show_currency=True", bot)
        self.assertIn("show_currency=False", core)
        self.assertEqual(bot.count("show_currency=True"), 1)

    def test_other_player_screens_do_not_read_current_balance(self):
        screens = (
            "ui/views/main_menu_view.py",
            "ui/views/player_view.py",
            "ui/views/shop_view.py",
            "ui/views/secret_realm_view.py",
            "ui/views/admin_view.py",
        )
        for relative in screens:
            with self.subTest(screen=relative):
                source = self.read(relative)
                self.assertNotIn("spirit_stones", source)
                self.assertNotIn("Linh thạch hiện có", source)
                self.assertNotIn("Túi linh thạch", source)

    def test_shop_can_show_prices_but_not_wallet_balance(self):
        shop = self.read("ui/views/shop_view.py")
        self.assertIn("item['price']", shop)
        self.assertNotIn("result['player'].spirit_stones", shop)
        self.assertNotIn("Còn lại:", shop)

    def test_insufficient_purchase_error_does_not_disclose_balance(self):
        economy = self.read("game/services/economy_service.py")
        self.assertIn("Không đủ linh thạch cho giao dịch này", economy)
        self.assertNotIn("có **{p.spirit_stones}**", economy)


if __name__ == "__main__":
    unittest.main()
