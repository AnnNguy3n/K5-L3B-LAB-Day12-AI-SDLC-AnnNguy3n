import json
import shlex
import subprocess
import tempfile
import unittest
from pathlib import Path

from chonoi.contract import DEFAULT_PATH, load_contract


class Phase4Submission(unittest.TestCase):
    def test_soak_ten_days_from_manifest_twice(self):
        manifest = load_contract(DEFAULT_PATH)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "soak.json"
            command = shlex.split(manifest["soak_cmd"]) + ["--days", "10", "--seed", "7", "--out", str(path)]
            runs = []
            for _ in range(2):
                subprocess.run(command, check=True, timeout=60)
                report = json.loads(path.read_text())
                self.assertGreater(report.pop("duration_s"), 0)
                self.assertEqual((report["days_completed"], report["crashes"]), (10, 0))
                self.assertEqual([r["day"] for r in report["results"]], list(range(1, 11)))
                self.assertTrue(all(r["harvested"] > 0 for r in report["results"]))
                self.assertGreater(report["results"][-1]["earned"], report["results"][4]["earned"])
                runs.append(report)
            self.assertEqual(*runs)

    def test_current_version_closing_payment_via_cli(self):
        manifest = load_contract(DEFAULT_PATH)
        fixture = {"quan":{"time_left_ticks":1, "random_customers":False, "customers":[{
            "id":"C2","table_id":"T1","dish_id":"goi_bong_sung","order_status":"served",
            "state":"eating","eat_ticks_left":30,"base_price":29,"tip":5}]}}
        with tempfile.TemporaryDirectory() as tmp:
            scenario, log = Path(tmp)/"scenario.json", Path(tmp)/"events.jsonl"
            scenario.write_text(json.dumps(fixture))
            subprocess.run(shlex.split(manifest["headless_cmd"]) + [
                "--rules",manifest["contract_version"],"--mode","quan","--seed","7","--ticks","1",
                "--scenario",str(scenario),"--out",str(log)],check=True)
            rows = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual([r["name"] for r in rows if r["type"] == "event"], ["paid","quan_end"])
            self.assertEqual(rows[1]["data"]["reason"], "closing")
            self.assertEqual(rows[-1]["earned"],34)

    def test_inventory_matches_last_morning_event_at_restaurant_open(self):
        manifest = load_contract(DEFAULT_PATH)
        cli = shlex.split(manifest["headless_cmd"]) + ["--rules",manifest["contract_version"],"--seed","7"]
        items = [{"id":"I10","kind":"bong_sung","fresh":30},
                 {"id":"I2","kind":"ca_loc","fresh":87.5}]
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            morning, evening, inventory = [folder / name for name in ("morning","evening","stock")]
            scenario, keys = folder / "scenario", folder / "keys"
            scenario.write_text(json.dumps({"gather":{"hold":items,"random_fish":False,"monsters":[]}}))
            keys.write_text(json.dumps({"frames":[{"tick":0,"interact":True}]}))
            subprocess.run(cli + ["--mode","gather","--ticks","1","--scenario",scenario,"--inputs",keys,
                                   "--out",morning,"--inventory-out",inventory],check=True)
            subprocess.run(cli + ["--mode","quan","--ticks","0","--inventory",inventory,"--out",evening],check=True)
            events = [json.loads(line) for line in morning.read_text().splitlines()]
            transfer = next(e["data"]["inventory"]["items"] for e in events if e.get("name") == "gather_end")
            stock = json.loads(evening.read_text().splitlines()[0])["stock"]
            self.assertEqual(stock, transfer)
            self.assertEqual([(i["id"],i["kind"]) for i in stock], [("I2","ca_loc"),("I10","bong_sung")])
            self.assertLess(stock[1]["fresh"],30)
