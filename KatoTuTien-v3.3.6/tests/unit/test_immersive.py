from __future__ import annotations

import random
import unittest

from game.engine import GameEngine, GameError


class ImmersiveGameplayTests(unittest.TestCase):
    def setUp(self):
        self.eng = GameEngine(":memory:", rng=random.Random(42))
        self.eng.players.create("u1", "Kato", "tien")

    def test_quest_progress_and_completion(self):
        r = self.eng.quests.start("u1", "mon_no_cua_lao_truong")
        self.assertEqual(r["step"]["kind"], "explore_zone")
        self.eng.quests.progress("u1", "explore_zone", "hoangnguyen", 2)
        active = self.eng.quests.active("u1")
        self.assertEqual(active[0]["step"]["kind"], "discovery")
        msgs = self.eng.quests.progress("u1", "discovery", "nguoi_la_bi_mat")
        self.assertTrue(any("món nợ" in x.lower() for x in msgs))
        status = self.eng.quests.status("u1", "mon_no_cua_lao_truong")
        self.assertTrue(status["step"].get("choices"))
        result = self.eng.quests.choose("u1", "mon_no_cua_lao_truong", "return")
        self.assertTrue(result["status"]["done"])
        self.assertEqual(self.eng.quests.active("u1"), [])
        rel = self.eng.npc.relationship("u1", "lao_truong")
        self.assertGreaterEqual(rel["affinity"], 5)

    def test_npc_and_world(self):
        self.assertTrue(self.eng.npc.list_npcs("u1"))
        npc = self.eng.npc.talk("u1", "lao_truong")
        self.assertIn("mon_no_cua_lao_truong", npc["quests"])
        # Force a deterministic world event through repository, avoiding spawn probability.
        self.eng.world.world.create("hon_hac_long", "yeuthusonmach", 1, 9999999999)
        result = self.eng.world.contribute("u1", "hon_hac_long")
        self.assertTrue(result["finished"])
        self.assertEqual(self.eng.world.active(), [])


if __name__ == "__main__":
    unittest.main()
