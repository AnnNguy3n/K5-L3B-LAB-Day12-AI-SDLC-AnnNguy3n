"""Kiểm phiên bản đang khai ở manifest qua tiến trình headless và snapshot."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from chonoi.contract import DEFAULT_PATH, load_contract
from chonoi.campaign import Campaign, BUTTONS
from chonoi.inputs import InputPlayer

TUNING = load_contract(DEFAULT_PATH)["tuning"]


def item(i, kind="ca_loc", fresh=100):
    return dict(id=i, kind=kind, fresh=fresh)


class CampaignContract(unittest.TestCase):
    def test_hold_to_stock_across_processes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sc, keys, inv, log = [root / name for name in ("sc","keys","inv","log")]
            sc.write_text(json.dumps({"gather":{"hold":[item("I7")],"monsters":[]}}))
            keys.write_text('{"frames":[{"tick":0,"interact":true}]}')
            cmd = ["python3","-m","chonoi.headless","--seed","1","--out",str(log)]
            subprocess.run(cmd+["--mode","gather","--ticks","1","--inventory-out",inv,"--inputs",keys,"--scenario",sc],check=True)
            actual = json.loads(inv.read_text())["items"]
            self.assertEqual(actual[0]["id"], "I7")
            self.assertAlmostEqual(actual[0]["fresh"], 100-0.5/60)
            subprocess.run(cmd+["--mode","quan","--ticks","0","--inventory",inv],check=True)
            snap = json.loads(log.read_text().splitlines()[0])
            self.assertEqual(snap["stock"][0]["id"],"I7")
            self.assertAlmostEqual(snap["stock"][0]["fresh"],actual[0]["fresh"],places=2)
            inv.write_text('{"items":{"ca_loc":1}}')
            log.unlink()
            result = subprocess.run(cmd+["--mode","quan","--ticks","0","--inventory",inv],capture_output=True)
            self.assertEqual(result.returncode,2)
            self.assertFalse(log.exists())

    def test_reassignment_and_price_after_decay(self):
        game = Campaign("quan", TUNING, {"player":{"pos":[2,8]}, "stock":[item("I1",fresh=30),item("I2",fresh=80)],
            "customers":[{"id":"C1","dish_id":"ca_loc_nuong_trui","table_id":"T1","reserved":["I1"]}]}, 1)
        game.step(InputPlayer([{"tick":0,"interact":True}]).advance(0))
        self.assertEqual([r["name"] for r in game.events],["spoiled","cook_started"])
        self.assertEqual(game.events[-1]["data"]["items"][0]["id"],"I2")
        self.assertEqual(game.events[-1]["data"]["base_price"],47)

    def test_last_tick_service_paid_with_no_tip(self):
        dish = {"order_id":"C9","dish_id":"goi_bong_sung","base_price":39}
        game = Campaign("quan",TUNING,{"time_left_ticks":1,"hand":dish,"player":{"pos":[9,2]},
            "customers":[{"id":"C9","table_id":"T1","dish_id":dish["dish_id"],"order_status":"assigned",
                          "patience_ticks_left":1}]},1)
        game.step(InputPlayer([{"tick":0,"interact":True}]).advance(0))
        self.assertEqual([r["name"] for r in game.events],["served","paid","quan_end"])
        self.assertEqual(game.events[1]["data"],dict(order_id="C9",table_id="T1",base_price=39,tip=0,amount=39,reason="closing"))
        self.assertEqual(game.reputation,3)

    def test_monster_loss_order_and_invulnerability(self):
        game = Campaign("gather",TUNING,{"player":{"pos":[60,24]},"hold":[item("I1"),item("I2"),item("I3"),item("I4")]},1)
        ip = InputPlayer([])
        game.step(ip.advance(0))
        hit = next(r["data"] for r in game.events if r["name"]=="monster_hit")
        self.assertEqual([i["id"] for i in hit["lost"]],["I4","I3"])
        self.assertEqual(game.sim.hp,2)
        game.step(ip.advance(1))
        self.assertFalse(any(r["name"]=="monster_hit" for r in game.events))

    def test_same_seed_and_spawning(self):
        def schools():
            game = Campaign("gather",TUNING,{},7)
            self.assertEqual(len(game.sim.fish),8)
            ip = InputPlayer([])
            for t in range(360):
                game.step(ip.advance(t))
            self.assertEqual([r["name"] for r in game.events],["fish_spawned"])
            return game.sim.fish
        self.assertEqual(schools(),schools())

    def test_pause_shop_and_next_day(self):
        game = Campaign("day",TUNING,{"day":{"earned":200,"money":200},"gather":{"time_left_ticks":1},
                        "quan":{"time_left_ticks":1}},1,2)
        frames = [{"tick":0,"pause":True},{"tick":1,"pause":False},{"tick":2,"pause":True},
                  {"tick":4,"shop_done":True}]
        ip=InputPlayer(frames,BUTTONS)
        for t in range(2):
            game.step(ip.advance(t))
        self.assertEqual(game.sim_tick,0)
        game.step(ip.advance(2))
        self.assertEqual((game.phase,game.phase_tick),("quan",0))
        game.step(ip.advance(3))
        game.step(ip.advance(4),"oxygen")
        self.assertEqual((game.day, game.money, game.earned, game.sim.oxygen_max),(2,0,200,2700))
        for t in range(5,607):
            game.step(ip.advance(t))
        self.assertTrue(game.done)
        self.assertEqual(game.completed,2)

    def test_live_buttons_and_menus_use_campaign_results(self):
        from chonoi.live import CampaignLive
        game = CampaignLive("day", TUNING, {"gather":{"time_left_ticks":1},"quan":{"time_left_ticks":1}},1,days=1)
        game._tick_once()
        self.assertEqual(game.session.tick,0)
        game.navigate("next")
        game.navigate("next")
        game._tick_once()
        self.assertEqual(game.screen,"evening")
        game.navigate("next")
        game.set_input({"pause":True})
        game._tick_once()
        self.assertTrue(game.session.paused)
        game.navigate("next")
        game._tick_once()
        self.assertEqual(game.screen,"result")
        game.navigate("next")
        game.set_input({"shop_done":True})
        game._tick_once()
        self.assertTrue(json.loads(game.state_json())["finished"])

    def test_spoiled_threshold_is_strict_and_one_shot(self):
        game = Campaign("gather", TUNING, {"hold":[item("I10",fresh=30),item("I2",fresh=30)],
                        "random_fish":False,"monsters":[]},1)
        ip = InputPlayer([])
        game.step(ip.advance(0))
        self.assertEqual([r["data"]["item_id"] for r in game.events],["I2","I10"])
        game.step(ip.advance(1))
        self.assertEqual(game.events,[])

    def test_demo_proof(self):
        subprocess.run(["python3","tools/check_submission.py"],check=True,capture_output=True)
