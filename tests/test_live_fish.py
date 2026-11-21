import unittest

from chonoi.contract import load_contract
from chonoi.live import LiveGame


class LiveFishTests(unittest.TestCase):
    def run_river(self, seed):
        game = LiveGame("day", load_contract()["tuning"], {
            "player": {"pos": [15, 5]}, "fish": [
                {"id": "F10", "kind": "ca_loc", "pos": [15, 5]},
                {"id": "F2", "kind": "ca_linh", "pos": [100, 9]}]}, seed)
        game.set_input({"catch": True})
        game._tick_once()
        sim = game.session.sim
        self.assertEqual(sim.hold, ["ca_loc"])
        self.assertLess(sim.fish[0]["pos"][0], 100)
        self.assertEqual(sim.fish[0]["heading_deg"], 180)
        for _ in range(game.river_fish.interval - 2):
            game._tick_once()
        self.assertEqual(len(sim.fish), 1)
        game._tick_once()
        self.assertEqual([f["id"] for f in sim.fish], ["F2", "F11"])
        self.assertGreater(sim.fish[-1]["pos"][1], sim.t["surface_depth"])
        return sim.snapshot()["fish"]

    def test_respawn_and_seed(self):
        self.assertEqual(self.run_river(7), self.run_river(7))
        self.assertNotEqual(self.run_river(8), self.run_river(7))

    def test_standalone_gather_keeps_original_fish(self):
        game = LiveGame("gather", load_contract()["tuning"], {}, 1)
        before = game.session.snapshot()["fish"]
        game._tick_once()
        self.assertEqual(before, game.session.snapshot()["fish"])
