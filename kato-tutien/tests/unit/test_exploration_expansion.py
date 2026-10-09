from __future__ import annotations

import random
import unittest

from game.content.events import CHOICE_EVENTS, EXPLORATION_EVENTS
from game.content.monsters import BOSS_MONSTERS, MONSTERS
from game.content.zones import EXPLORE_ZONES
from game.content.items import ITEMS
from game.engine import GameEngine


class ExplorationExpansionTests(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(":memory:", rng=random.Random(17))
        self.engine.players.create("explorer", "Explorer", "ma")
        self.player = self.engine.players.get("explorer")
        self.player.last_explore = 0
        self.player.last_hunt = 0
        self.player.realm_index = 10
        self.player.explore_zone = "hukhong"
        self.player.hp = self.player.max_hp
        self.engine._players.save(self.player)

    def test_bestiary_grew_and_has_unique_names(self):
        self.assertGreaterEqual(len(MONSTERS), 25)
        self.assertGreaterEqual(len(BOSS_MONSTERS), 12)
        self.assertEqual(len({m["name"] for m in MONSTERS}), len(MONSTERS))
        self.assertEqual(len({m["name"] for m in BOSS_MONSTERS}), len(BOSS_MONSTERS))

    def test_new_endgame_regions_exist_and_are_gated(self):
        self.assertEqual(EXPLORE_ZONES["vancotlang"]["min_realm"], 8)
        self.assertEqual(EXPLORE_ZONES["hukhong"]["min_realm"], 10)
        self.assertEqual(EXPLORE_ZONES["vancotlang"]["path"], "ma")

    def test_exploration_pools_are_substantially_larger(self):
        self.assertGreaterEqual(len(EXPLORATION_EVENTS), 18)
        self.assertGreaterEqual(len(CHOICE_EVENTS), 8)

    def test_all_event_zone_and_item_references_are_valid(self):
        all_zone_keys = set(EXPLORE_ZONES)
        for event in [*EXPLORATION_EVENTS, *CHOICE_EVENTS]:
            self.assertTrue(set(event.get("zones", [])) <= all_zone_keys, event["key"])
            for choice in event.get("choices", []):
                item_id = choice.get("effect", {}).get("item")
                if item_id:
                    self.assertIn(item_id, ITEMS, (event["key"], item_id))
            item_id = event.get("item")
            if item_id:
                self.assertIn(item_id, ITEMS, (event["key"], item_id))

    def test_zone_encounter_uses_local_high_tier_creature(self):
        enc = self.engine.combat.start_encounter("explorer", zone_key="hukhong")
        self.assertIn(enc.enemy_name, {m["name"] for m in MONSTERS if "hukhong" in m.get("zones", [])})
        self.assertGreater(enc.enemy_max_hp, 1000)

    def test_boss_pool_contains_region_specific_endgame_boss(self):
        enc = self.engine.combat.start_encounter("explorer", boss=True, zone_key="hukhong")
        self.assertIn(enc.enemy_name, {b["name"] for b in BOSS_MONSTERS if "hukhong" in b.get("zones", [])})
        self.assertTrue(enc.is_boss)
        self.assertGreater(enc.enemy_max_hp, 2500)

    def test_high_level_boss_stays_in_selected_region(self):
        self.player.realm_index = 11
        self.player.explore_zone = "vancotlang"
        self.engine._players.save(self.player)
        enc = self.engine.combat.start_encounter("explorer", boss=True, zone_key="vancotlang")
        self.assertIn(enc.enemy_name, {b["name"] for b in BOSS_MONSTERS if "vancotlang" in b.get("zones", [])})

    def test_elite_is_marked_and_has_scaled_stats(self):
        normal = self.engine.combat.start_encounter("explorer", zone_key="hukhong")
        elite = self.engine.combat.start_encounter("explorer", zone_key="hukhong", elite=True)
        self.assertTrue(elite.is_elite)
        self.assertIn("Tinh Anh", elite.enemy_name)
        self.assertGreater(elite.enemy_max_hp, normal.enemy_max_hp)


if __name__ == "__main__":
    unittest.main()
