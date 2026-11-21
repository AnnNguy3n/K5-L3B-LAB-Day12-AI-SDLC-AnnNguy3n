"""Luật Phase 1 và bàn giao kho qua CLI thực."""
import json
import tempfile
import unittest
from pathlib import Path

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import InputPlayer
from chonoi.runner import Session
from helpers import events, read_jsonl, run_headless

FIXTURES = Path(__file__).parent / "fixtures" / "phase-1"


def simulate(mode, scenario, ticks, frames=()):
    session = Session(mode, load_contract()["tuning"], scenario, 1)
    inputs = InputPlayer(frames)
    log = []
    for tick in range(ticks):
        log.extend(session.step(inputs.advance(tick)))
        if session.done:
            break
    return session.snapshot(), log


class GatherRules(unittest.TestCase):
    def test_last_breath_then_faint(self):
        tuning = load_contract()["tuning"]["gather"]
        s, log = simulate("gather", {"hold": ["ca_loc"], "player": {
            "pos": [10, 4], "oxygen_ticks": 1, "hp": 1}}, tuning["choke_interval_ticks"])
        self.assertEqual([e["name"] for e in log], ["oxygen_empty", "choke", "faint", "gather_end"])
        self.assertEqual(s["hold"], [])
        self.assertEqual(log[-1]["data"], {"reason": "fainted", "inventory": {"items": {}}})

    def test_dive_surface_refill(self):
        s, log = simulate("gather", {"player": {"pos": [12, 0.5], "oxygen_ticks": 10}}, 12, [
            {"tick": 0, "move": [0, 1]}, {"tick": 3, "move": [0, -1]}])
        self.assertEqual([e["name"] for e in log], ["dive", "surface"])
        self.assertGreater(s["player"]["oxygen_ticks"], 10)

    def test_regrow_then_pick_by_numeric_id(self):
        nodes = [{"id": i, "kind": "bong_sung", "pos": [12, 0], "regrow_ticks": 1} for i in ("N10", "N2")]
        s, log = simulate("gather", {"nodes": nodes, "player": {"pos": [12, 0]}}, 2,
                          [{"tick": 0, "interact": True}])
        self.assertEqual([e["name"] for e in log], ["node_regrown", "node_regrown", "gather"])
        self.assertEqual(log[-1]["data"]["node_id"], "N2")
        self.assertEqual(s["hold"], ["bong_sung"])
        self.assertFalse(s["nodes"][0]["ready"])

    def test_fish_yield_exceeds_free_space(self):
        capacity = load_contract()["tuning"]["gather"]["hold_capacity"]
        hold = ["ca_loc"] * (capacity - 1)
        s, log = simulate("gather", {"hold": hold, "player": {"pos": [15, 5]}}, 1, [{"tick": 0, "catch": True}])
        self.assertEqual([e["name"] for e in log], ["hold_full"])
        self.assertEqual(s["hold"], hold)
        self.assertIn("F1", [f["id"] for f in s["fish"]])

    def test_cooldown_blocks_second_catch(self):
        fish = [{"id": i, "kind": "ca_loc", "pos": [15, 5]} for i in ("F1", "F2")]
        s, log = simulate("gather", {"player": {"pos": [15, 5]}, "fish": fish}, 3, [
            {"tick": 0, "catch": True}, {"tick": 1, "catch": False}, {"tick": 2, "catch": True}])
        self.assertEqual(len(events(log, "fish_caught")), 1)
        self.assertEqual(s["hold"], ["ca_loc"])


class QuanRules(unittest.TestCase):
    def test_no_dish_with_empty_stock(self):
        tick = load_contract()["tuning"]["quan"]["first_customer_tick"]
        s, log = simulate("quan", {}, tick)
        self.assertEqual([e["name"] for e in log], ["no_dish"])
        self.assertFalse(s["customers"])

    def test_serve_at_patience_deadline(self):
        dish = "ca_loc_nuong_trui"
        s, log = simulate("quan", {"player": {"pos": [9, 2]}, "hand": {"order_id": "C1", "dish_id": dish, "base_price": 60}, "customers": [
            {"id": "C1", "dish_id": dish, "table_id": "T1", "order_status": "assigned", "patience_ticks_left": 1}]},
            1, [{"tick": 0, "interact": True}])
        self.assertEqual([e["name"] for e in log], ["served"])
        self.assertIsNone(s["hand"])
        self.assertEqual(s["customers"][0]["state"], "eating")

    def test_reserved_stock_and_dish_consistency(self):
        customer = {"id": "C1", "table_id": "T1", "dish_id": "ca_loc_nuong_trui"}
        for scenario in ({"customers": [customer]}, {"customers": [dict(customer, order_status="assigned")]},
                         {"customers": [dict(customer, state="eating", eat_ticks_left=2)]}):
            with self.subTest(scenario=scenario), self.assertRaises(BadInput):
                simulate("quan", scenario, 0)

    def test_replay_from_empty_hold_to_payment(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            runs = []
            for run in range(2):
                stock = root / f"stock{run}.json"
                outputs = []
                for mode, ticks in (("gather", 100), ("quan", 1300)):
                    output = root / f"{mode}{run}.jsonl"
                    code, err = run_headless("--mode", mode, "--seed", "1", "--ticks", str(ticks),
                        "--scenario", FIXTURES / f"{mode}.json", "--inputs", FIXTURES / f"{mode}-inputs.json",
                        "--out", output, "--inventory-out" if mode == "gather" else "--inventory", stock)
                    self.assertEqual(code, 0, err)
                    outputs.append(output.read_bytes())
                self.assertEqual(json.loads(stock.read_text()), {"items": {"ca_loc": 1}})
                rows = read_jsonl(output)
                self.assertEqual([e["name"] for e in events(rows)], [
                    "customer_arrived", "cook_started", "dish_ready", "dish_picked", "served", "paid", "quan_end"])
                self.assertEqual(rows[-2]["stock"], {})
                self.assertEqual(rows[-1]["money"], 72)
                runs.append(outputs)
            self.assertEqual(*runs)
