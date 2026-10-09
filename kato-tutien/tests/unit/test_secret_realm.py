from __future__ import annotations

import random
import tempfile
import unittest
from pathlib import Path

from game.engine import GameEngine, GameError
from game.rules.cultivation_rules import cultivation_requirement


class SecretRealmTests(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(":memory:", rng=random.Random(7))
        self.engine.players.create("realm-user", "Realm Tester", "tien")
        player = self.engine.players.get("realm-user")
        player.realm_index = 1
        player.realm_layer = 1
        player.cultivation = 0
        self.engine._players.save(player)
        self.now = 1_800_000_000
        self.engine.secret_realm.clock = lambda: self.now

    def tearDown(self):
        self.engine.db.close()

    def test_requires_three_hours_and_claims_once(self):
        started = self.engine.secret_realm.select("realm-user", "thanh_van")
        self.assertEqual(started["realm"]["key"], "thanh_van")
        with self.assertRaises(GameError):
            self.engine.secret_realm.claim("realm-user")

        self.now += 3 * 60 * 60
        before = self.engine.players.get("realm-user")
        result = self.engine.secret_realm.claim("realm-user")
        after = self.engine.players.get("realm-user")
        self.assertGreaterEqual(result["stones"], 300)
        self.assertLessEqual(result["stones"], 600)
        self.assertGreaterEqual(result["cultivation"], 100)
        self.assertLessEqual(result["cultivation"], 200)
        self.assertEqual(after.spirit_stones - before.spirit_stones, result["stones"])
        self.assertEqual(after.cultivation - before.cultivation, result["cultivation"])
        self.assertFalse(self.engine.secret_realm.status("realm-user")["ready"])
        with self.assertRaises(GameError):
            self.engine.secret_realm.claim("realm-user")

    def test_same_realm_click_does_not_reset_timer_and_switch_is_blocked(self):
        first = self.engine.secret_realm.select("realm-user", "thanh_van")
        start_at = first["session"]["cycle_started_at"]
        self.now += 120
        again = self.engine.secret_realm.select("realm-user", "thanh_van")
        self.assertEqual(again["session"]["cycle_started_at"], start_at)
        player = self.engine.players.get("realm-user")
        player.realm_index = 2
        self.engine._players.save(player)
        with self.assertRaises(GameError):
            self.engine.secret_realm.select("realm-user", "linh_thach")

    def test_leaving_early_discards_session(self):
        self.engine.secret_realm.select("realm-user", "thanh_van")
        self.now += 60
        result = self.engine.secret_realm.leave("realm-user")
        self.assertEqual(result["remaining_lost"], 3 * 60 * 60 - 60)
        self.assertIsNone(self.engine.secret_realm.status("realm-user")["session"])

    def test_cultivation_reward_does_not_skip_breakthrough_stage(self):
        player = self.engine.players.get("realm-user")
        required = cultivation_requirement(player.realm_index, player.realm_layer)
        player.cultivation = required - 5
        self.engine._players.save(player)
        self.engine.secret_realm.select("realm-user", "thanh_van")
        self.now += 3 * 60 * 60
        result = self.engine.secret_realm.claim("realm-user")
        self.assertEqual(result["cultivation"], 5)
        self.assertTrue(result["clamped_cultivation"])
        self.assertEqual(self.engine.players.get("realm-user").cultivation, required)

    def test_active_session_survives_engine_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = str(Path(directory) / "secret-realm.db")
            first = GameEngine(database_path, rng=random.Random(3))
            first.players.create("persisted-user", "Persistent", "tien")
            player = first.players.get("persisted-user")
            player.realm_index = 1
            first._players.save(player)
            current_time = 1_850_000_000
            first.secret_realm.clock = lambda: current_time
            first.secret_realm.select("persisted-user", "thanh_van")
            first.db.close()

            reopened = GameEngine(database_path, rng=random.Random(4))
            reopened.secret_realm.clock = lambda: current_time + 120
            state = reopened.secret_realm.status("persisted-user")
            self.assertEqual(state["session"]["realm_key"], "thanh_van")
            self.assertEqual(state["remaining"], 3 * 60 * 60 - 120)
            reopened.db.close()

    def test_locked_realm_cannot_be_entered(self):
        with self.assertRaises(GameError):
            self.engine.secret_realm.select("realm-user", "linh_thach")


if __name__ == "__main__":
    unittest.main()
