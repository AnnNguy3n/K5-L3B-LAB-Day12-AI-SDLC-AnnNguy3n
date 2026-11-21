import json
import unittest

from tools.demo_day import play


class ReceiptTest(unittest.TestCase):
    def test_full_day_receipt_and_reset(self):
        game = play()
        state = json.loads(game.state_json())
        self.assertTrue(state["finished"])
        self.assertEqual(state["day"]["morning"]["items"], {"ca_loc": 1})
        self.assertEqual((state["day"]["meals_paid"], state["day"]["tips"]), (1, 12))
        self.assertEqual((state["earned"], state["score"]), (72, 372))
        game.restart()
        self.assertEqual(json.loads(game.state_json())["day"], {"morning": None, "meals_paid": 0, "tips": 0})
