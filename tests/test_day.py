import json
import unittest

from chonoi.contract import load_contract
from chonoi.live import LiveGame


class DayTests(unittest.TestCase):
    def game(self, morning):
        return LiveGame("day", load_contract()["tuning"], morning, 1)

    def test_dock_transfers_hold_and_restart_clears_day(self):
        game = self.game({"hold": ["ca_loc"]})
        game.set_input({"interact": True})
        game._tick_once()
        state = json.loads(game.state_json())
        self.assertEqual(state["day"]["morning"], {"reason": "docked", "items": {"ca_loc": 1}})
        self.assertEqual(state["mode"], "quan")
        self.assertEqual(state["stock"], {"ca_loc": 1})
        game.restart()
        self.assertEqual(game.session.mode, "gather")
        self.assertIsNone(json.loads(game.state_json())["day"]["morning"])

    def test_timeout_and_faint_transfer_once(self):
        for morning, stock, reason in [
            ({"hold": ["bong_sung"], "time_left_ticks": 1}, {"bong_sung": 1}, "time"),
            ({"hold": ["ca_loc"], "player": {"hp": 1, "oxygen_ticks": 0,
              "zero_oxy_ticks": 59, "pos": [5, 4]}}, {}, "fainted")]:
            with self.subTest(reason=reason):
                game = self.game(morning)
                game._tick_once()
                game._tick_once()
                self.assertEqual(game.session.tick, 1)
                self.assertEqual(game.session.snapshot()["stock"], stock)
                self.assertEqual(game.morning_result["reason"], reason)
