from __future__ import annotations

import random
import unittest

from game.engine import GameEngine, GameError
from game.models.combat import Encounter


class CombatSkillStabilityTests(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(":memory:", rng=random.Random(17))
        self.player = self.engine.players.create("skill-user", "Skill User", "tien")
        self.player.spirit_stones = 100_000
        self.engine._players.save(self.player)
        self.engine.economy.buy("skill-user", "ngu_hanh_quyet", 1)
        self.engine.economy.learn_technique("skill-user", "ngu_hanh_quyet")

    def test_learned_technique_can_be_used_and_increases_mastery(self):
        enc = self.engine.combat.start_encounter("skill-user")
        enc.enemy_hp = enc.enemy_max_hp = 100_000
        enc.enemy_attack = 1
        before_hp = enc.enemy_hp
        before_mastery = self.engine._players.get_mastery("skill-user", "ngu_hanh_quyet")["mastery"]

        result = self.engine.combat.skill("skill-user", "ngu_hanh_quyet")

        self.assertIn("encounter", result)
        self.assertLess(result["encounter"].enemy_hp, before_hp)
        self.assertEqual(result["encounter"].turn_number, 1)
        after_mastery = self.engine._players.get_mastery("skill-user", "ngu_hanh_quyet")["mastery"]
        self.assertEqual(after_mastery, min(12, before_mastery + 1))

    def test_unlearned_skill_does_not_consume_a_turn(self):
        enc = self.engine.combat.start_encounter("skill-user")
        before_hp = enc.enemy_hp

        with self.assertRaises(GameError):
            self.engine.combat.skill("skill-user", "pha_quan_dao")

        self.assertEqual(enc.enemy_hp, before_hp)
        self.assertEqual(enc.turn_number, 0)

    def test_broken_technique_reference_is_rejected_safely(self):
        enc = self.engine.combat.start_encounter("skill-user")
        self.engine._players.add_discovery("skill-user", "technique:deleted_technique")

        with self.assertRaises(GameError):
            self.engine.combat.skill("skill-user", "deleted_technique")

        self.assertEqual(enc.turn_number, 0)

    def test_cannot_overwrite_an_active_encounter(self):
        active = self.engine.combat.start_encounter("skill-user")
        with self.assertRaises(GameError):
            self.engine.combat.start_encounter("skill-user", boss=True)
        self.assertIs(self.engine.combat.get_encounter("skill-user"), active)

    def test_explore_and_hunt_do_not_consume_cooldown_during_fight(self):
        self.engine.combat.start_encounter("skill-user")
        before = self.engine.players.get("skill-user")
        last_explore, last_hunt = before.last_explore, before.last_hunt

        with self.assertRaises(GameError):
            self.engine.exploration.explore("skill-user")
        with self.assertRaises(GameError):
            self.engine.exploration.hunt("skill-user")

        after = self.engine.players.get("skill-user")
        self.assertEqual(after.last_explore, last_explore)
        self.assertEqual(after.last_hunt, last_hunt)

    def test_encounter_turn_number_serializes_backwards_compatibly(self):
        enc = Encounter(
            player_id="skill-user", enemy_name="Test Beast", enemy_hp=30,
            enemy_max_hp=30, enemy_attack=4, enemy_defense=2,
            player_hp=100, player_max_hp=100, turn_number=4,
        )
        restored = Encounter.from_dict(enc.to_dict())
        self.assertEqual(restored.turn_number, 4)

        legacy = enc.to_dict()
        legacy.pop("turn_number")
        self.assertEqual(Encounter.from_dict(legacy).turn_number, 0)


if __name__ == "__main__":
    unittest.main()
