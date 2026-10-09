from __future__ import annotations

import random
import time
import unittest

from game.engine import GameEngine, GameError
from game.content.items import ITEMS
from game.content.realms import cultivation_requirement
from game.models.combat import Encounter
from game.rules.cultivation_rules import breakthrough_chance
from game.rules.economy_rules import stone_loot_multiplier


class EconomyAndStatBalanceTests(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(":memory:", rng=random.Random(17))

    def tearDown(self):
        self.engine.db.close()

    def make_player(self, user_id="u"):
        return self.engine.players.create(user_id, "Tester", "tien")

    def test_breakthrough_baseline_is_not_near_guaranteed(self):
        chance = breakthrough_chance(root=55, mind=55, insight=55, injury=0, dao_stage=0)
        self.assertAlmostEqual(chance, 0.58)
        self.assertLess(chance, 0.70)

    def test_breakthrough_chance_keeps_caps_and_injury_penalty(self):
        strong = breakthrough_chance(root=100, mind=100, insight=100, injury=0, dao_stage=5, foundation_bonus=0.2)
        injured = breakthrough_chance(root=55, mind=55, insight=55, injury=10, dao_stage=0)
        self.assertEqual(strong, 0.90)
        self.assertAlmostEqual(injured, 0.48)
        self.assertGreaterEqual(injured, 0.05)

    def test_new_character_stats_are_in_bounded_start_range(self):
        p = self.make_player()
        for key in ("root", "insight", "luck", "fate", "mind"):
            self.assertGreaterEqual(getattr(p, key), 35)
            self.assertLessEqual(getattr(p, key), 75)

    def test_item_cultivation_cannot_overfill_stage(self):
        p = self.make_player()
        p.realm_index = 1
        p.realm_layer = 1
        required = cultivation_requirement(p.realm_index, p.realm_layer)
        p.cultivation = required - 10
        self.engine._players.save(p)
        self.engine._inventory.add(p.user_id, "tu_khi_dan", 2)
        result = self.engine.economy.use_item(p.user_id, "tu_khi_dan", 2)
        self.assertEqual(result["cultivation_gained"], 10)
        self.assertEqual(self.engine.players.get(p.user_id).cultivation, required)

    def test_permanent_stat_bonus_from_same_item_is_only_granted_once(self):
        p = self.make_player()
        p.realm_index = 1
        p.realm_layer = 5
        self.engine._players.save(p)
        root_before = p.root
        self.engine._inventory.add(p.user_id, "qing_moc_phu", 2)
        self.engine.economy.use_item(p.user_id, "qing_moc_phu")
        after_first = self.engine.players.get(p.user_id)
        self.assertEqual(after_first.root, root_before + 1)
        self.engine.economy.use_item(p.user_id, "qing_moc_phu")
        after_second = self.engine.players.get(p.user_id)
        self.assertEqual(after_second.root, root_before + 1)
        self.assertEqual(after_second.cultivation, 600)

    def test_bulk_use_of_permanent_stat_item_is_rejected_without_consumption(self):
        p = self.make_player()
        self.engine._inventory.add(p.user_id, "qing_moc_phu", 2)
        with self.assertRaises(GameError):
            self.engine.economy.use_item(p.user_id, "qing_moc_phu", 2)
        self.assertEqual(self.engine._inventory.get_count(p.user_id, "qing_moc_phu"), 2)

    def test_daily_reward_streak_bonus_caps_at_thirty_days(self):
        p = self.make_player()
        now = int(time.time())
        p.last_daily = now - 24 * 60 * 60 - 5
        p.daily_streak = 30
        self.engine._players.save(p)
        result = self.engine.cultivation.claim_daily(p.user_id)
        self.assertEqual(result["streak"], 31)
        self.assertEqual(result["stones"], 2000)

    def test_luck_currency_bonus_has_a_twenty_five_percent_cap(self):
        self.assertEqual(stone_loot_multiplier(100), 1.25)
        self.assertEqual(stone_loot_multiplier(400), 1.25)
        self.assertEqual(stone_loot_multiplier(-10), 1.0)

    def test_exploration_reward_clamps_to_current_stage(self):
        p = self.make_player()
        p.realm_index = 1
        p.realm_layer = 1
        req = cultivation_requirement(p.realm_index, p.realm_layer)
        p.cultivation = req - 5
        result = {}
        self.engine.exploration._apply_effect(p, p.user_id, {"cultivation": 100}, result)
        self.assertEqual(result["cultivation"], 5)
        self.assertTrue(result["cultivation_clamped"])
        self.assertEqual(p.cultivation, req)

    def test_combat_reward_clamps_to_current_stage(self):
        p = self.make_player()
        p.realm_index = 1
        p.realm_layer = 1
        req = cultivation_requirement(p.realm_index, p.realm_layer)
        p.cultivation = req - 3
        self.engine._players.save(p)
        enc = Encounter(p.user_id, "Test Beast", 1, 1, 1, 0, p.hp, p.max_hp)
        self.engine.combat._encounters[p.user_id] = enc
        result = self.engine.combat._finish(enc, p, True, [])
        self.assertEqual(result["rewards"]["cultivation"], 3)
        self.assertEqual(self.engine.players.get(p.user_id).cultivation, req)

    def test_world_event_reward_clamps_to_current_stage(self):
        p = self.make_player()
        p.explore_zone = "yeuthusonmach"
        p.cultivation = cultivation_requirement(0, 1) - 5
        self.engine._players.save(p)
        self.engine.world.world.create("hon_hac_long", "yeuthusonmach", 1, int(time.time()) + 1000)
        result = self.engine.world.contribute(p.user_id, "hon_hac_long")
        self.assertEqual(result["cultivation"], 5)
        self.assertEqual(result["cultivation_requested"], 120)

    def test_final_quest_choice_is_saved_before_completion_reward(self):
        p = self.make_player()
        starting_stones = p.spirit_stones
        starting_fate = p.fate
        quest_key = "mon_no_cua_lao_truong"
        self.engine.quests.start(p.user_id, quest_key)
        self.engine._quests.update(p.user_id, quest_key, 2, 0)
        self.engine.quests.choose(p.user_id, quest_key, "return")
        saved = self.engine.players.get(p.user_id)
        self.assertEqual(saved.spirit_stones, starting_stones + 600 + 1200)
        self.assertEqual(saved.fate, min(100, starting_fate + 4))

    def test_breakthrough_only_items_do_not_advertise_unused_stats(self):
        for item_id, bonus in (("tru_co_dan", 0.05), ("kim_dan_dai_duoc", 0.08)):
            item = ITEMS[item_id]
            self.assertEqual(item["breakthrough_bonus"], bonus)
            self.assertNotIn("cultivation", item)
            self.assertNotIn("root", item)
            self.assertNotIn("insight", item)

    def test_equipment_thunder_resistance_descriptions_match_values(self):
        self.assertAlmostEqual(ITEMS["huyen_thiet_linh_kinh"]["thunder_resistance"], 0.05)
        self.assertIn("5%", ITEMS["huyen_thiet_linh_kinh"]["description"])
        self.assertAlmostEqual(ITEMS["thien_loi_chau"]["thunder_resistance"], 0.08)
        self.assertIn("8%", ITEMS["thien_loi_chau"]["description"])

    def test_healing_respects_equipped_max_hp_without_lowering_existing_hp(self):
        p = self.make_player()
        p.loadout = {"armor": "kim_cang_giap"}
        effective_max_hp = self.engine.combat.battle_stats(p)["max_hp"]
        p.hp = p.max_hp + 15
        self.engine._players.save(p)
        self.engine._inventory.add(p.user_id, "hoi_huyet_dan", 1)

        result = self.engine.economy.use_item(p.user_id, "hoi_huyet_dan")
        saved = self.engine.players.get(p.user_id)

        self.assertEqual(saved.hp, effective_max_hp)
        self.assertIn(f"+5 HP", result["notes"])

    def test_tribulation_uses_combat_effective_max_hp(self):
        p = self.make_player()
        p.loadout = {"armor": "kim_cang_giap"}
        self.engine._players.save(p)
        expected_max_hp = self.engine.combat.battle_stats(p)["max_hp"]

        result = self.engine.cultivation._resolve_nine_thunder(p, 1)
        preview = self.engine.cultivation.breakthrough_preview(p.user_id)

        self.assertEqual(result["max_hp"], expected_max_hp)
        self.assertEqual(preview["max_hp"], expected_max_hp)

    def test_unequipping_hp_gear_clamps_hp_to_the_new_effective_max(self):
        p = self.make_player()
        p.talent = "Thanh Tâm"
        p.loadout = {"armor": "kim_cang_giap"}
        p.hp = self.engine.combat.battle_stats(p)["max_hp"]
        self.engine._players.save(p)

        result = self.engine.economy.unequip(p.user_id, "armor")
        saved = self.engine.players.get(p.user_id)
        expected_max_hp = self.engine.combat.battle_stats(saved)["max_hp"]

        self.assertEqual(saved.hp, expected_max_hp)
        self.assertEqual(result["power"]["max_hp"], expected_max_hp)

    def test_defeat_applies_declared_small_stone_loss_and_effective_hp(self):
        p = self.make_player()
        p.talent = "Thanh Tâm"
        p.spirit_stones = 10_000
        p.loadout = {"armor": "kim_cang_giap"}
        self.engine._players.save(p)
        max_hp = self.engine.combat.battle_stats(p)["max_hp"]
        encounter = Encounter(p.user_id, "Test Beast", 50, 50, 10, 0, 0, max_hp)

        result = self.engine.combat._finish(encounter, p, False, [])
        saved = self.engine.players.get(p.user_id)

        self.assertEqual(saved.spirit_stones, 9_900)
        self.assertEqual(saved.hp, int(max_hp * 0.3))
        self.assertTrue(any("100 linh thạch" in line for line in result["logs"]))

    def test_healing_normalizes_legacy_hp_above_current_cap(self):
        p = self.make_player()
        p.talent = "Thanh Tâm"
        p.hp = p.max_hp + 25
        self.engine._players.save(p)
        self.engine._inventory.add(p.user_id, "hoi_huyet_dan", 1)

        self.engine.economy.use_item(p.user_id, "hoi_huyet_dan")
        saved = self.engine.players.get(p.user_id)

        self.assertEqual(saved.hp, self.engine.combat.battle_stats(saved)["max_hp"])


if __name__ == "__main__":
    unittest.main()
