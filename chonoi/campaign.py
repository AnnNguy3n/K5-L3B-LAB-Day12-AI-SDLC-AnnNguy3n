"""Điều phối tick ngoài, pause và ba pha của Test Contract v1.2."""
import math
from collections import Counter
from .errors import BadInput
from .ids import IdAllocator
from .inputs import InputPlayer
from .inventory import write_inventory
from .jsonl import JsonlWriter
from .rng import Streams
from .sim.fresh import FreshGather, FreshQuan

BUTTONS = ("interact", "catch", "pause", "shop_done", "attack", "photo")


class Campaign:
    def __init__(self, mode, tuning, scenario, seed, days=1, inventory=None):
        self.mode, self.tuning, self.days = mode, tuning, days
        self.parts = scenario if mode == "day" else {mode: scenario}
        self.ids, self.streams = IdAllocator(), Streams(seed)
        self.day, self.completed = 1, 0
        self.tick = self.sim_tick = self.phase_tick = 0
        self.paused = self.done = False
        self.reason = "tick_limit"
        day = self.parts.get("day", {})
        if not isinstance(day, dict) or set(day) - {"earned", "money", "reputation", "upgrades", "day_plan"}:
            raise BadInput("khối day không hợp lệ")
        self.money, self.earned = day.get("money", 0), day.get("earned", 0)
        if (("money" in day) != ("earned" in day) or type(self.money) is not int or
                type(self.earned) is not int or not 0 <= self.money <= self.earned):
            raise BadInput("tiền đầu ngày không hợp lệ")
        self.reputation = day.get("reputation", tuning["quan"]["reputation_initial"])
        if type(self.reputation) not in (int,float) or not tuning["quan"]["reputation_min"] <= self.reputation <= tuning["quan"]["reputation_max"]:
            raise BadInput("uy tín đầu ngày ngoài miền")
        if not isinstance(day.get("upgrades", {}), dict):
            raise BadInput("upgrades cần là object")
        self.upgrades = dict(day.get("upgrades", {}))
        for key, level in self.upgrades.items():
            if key not in tuning["shop"]["upgrades"] or type(level) is not int or not 0 <= level <= len(tuning["shop"]["upgrades"][key]):
                raise BadInput("cấp nâng cấp không hợp lệ")
        self.active = dict(self.upgrades)
        self.plans = {p["day"]: p for p in tuning["day_plan"]}
        overrides = day.get("day_plan", [])
        if not isinstance(overrides, list):
            raise BadInput("day_plan cần là mảng")
        seen = set()
        for entry in overrides:
            if (not isinstance(entry, dict) or set(entry) - {"day","dishes","ingredients"}
                    or type(entry.get("day")) is not int or entry["day"] in seen
                    or not isinstance(entry.get("dishes"), dict) or not entry["dishes"]):
                raise BadInput("mục day_plan không hợp lệ")
            seen.add(entry["day"])
            needs = Counter()
            dishes = entry["dishes"]
            for key, count in dishes.items():
                if key not in tuning["menu"] or type(count) is not int or count <= 0:
                    raise BadInput("kế hoạch món không hợp lệ")
                for kind, units in tuning["menu"][key]["recipe"].items():
                    needs[kind] += units * count
            if entry.get("ingredients", needs) != needs or entry["day"] not in self.plans:
                raise BadInput("kế hoạch ngày mâu thuẫn")
            self.plans[entry["day"]] = dict(entry, ingredients=dict(needs))
        self.events = []
        if mode == "quan":
            self.open_quan(inventory)
            self.reputation = self.sim.reputation
        else:
            self.open_morning()

    def event(self, name, data):
        row = dict(type="event", tick=self.tick, phase=self.phase, name=name, data=data)
        if self.mode == "day":
            row["day"] = self.day
        self.events.append(row)

    def open_morning(self):
        self.phase, self.phase_tick = "gather", 0
        config = dict(self.tuning["gather"])
        self.active = dict(self.upgrades)
        for key, level in self.active.items():
            if level:
                row = self.tuning["shop"]["upgrades"][key][level-1]
                config.update({k: v for k, v in row.items() if k not in ("price", "level")})
        morning = dict(self.parts.get("gather", {}))
        if self.day > 1:
            morning["hold"] = [dict(i, id=self.ids.new("I")) for i in morning.get("hold", [])]
        self.sim = FreshGather(dict(self.tuning, gather=config), morning, self.streams, self.ids, self.day)
        self.plan = self.plans[self.day]
        if self.mode == "day":
            self.event("day_start", {})
            self.event("day_plan", {k: self.plan[k] for k in ("dishes", "ingredients")})
            self.event("phase_start", {})

    def open_quan(self, inventory):
        self.phase, self.phase_tick = "quan", 0
        self.sim = FreshQuan(self.tuning, self.parts.get("quan", {}), self.streams, self.ids, inventory)
        if self.mode == "day":
            self.sim.allowed_dishes = set(self.plan["dishes"])
            self.sim.money, self.sim.earned, self.sim.reputation = self.money, self.earned, self.reputation
            self.event("phase_start", {})

    def step(self, inp, buy=None):
        self.events = []
        if self.done:
            return
        self.tick += 1
        if inp.pressed("pause"):
            self.paused = not self.paused
            self.event("paused" if self.paused else "resumed", {})
        if self.paused:
            return
        self.sim_tick += 1
        self.phase_tick += 1
        if self.phase == "shop":
            self.shop_tick(inp, buy)
            return
        for name, data in self.sim.step(inp):
            self.event(name, data)
        if self.phase == "quan":
            self.money, self.earned, self.reputation = self.sim.money, self.sim.earned, self.sim.reputation
        if self.sim.done:
            if self.mode != "day":
                self.done, self.reason = True, self.sim.reason
            elif self.phase == "gather":
                self.open_quan(self.sim.inventory_items())
            else:
                self.phase, self.phase_tick = "shop", 0
                self.shop_time = self.tuning["shop"]["max_ticks"]
                self.event("phase_start", {})

    def shop_tick(self, inp, buy):
        self.shop_time = max(0, self.shop_time - 1)
        if buy:
            levels = self.tuning["shop"]["upgrades"].get(buy)
            level = self.upgrades.get(buy, 0)
            if levels is None:
                reason = "unknown"
            elif level >= len(levels):
                reason = "max_level"
            elif self.money < levels[level]["price"]:
                reason = "funds"
            else:
                price = levels[level]["price"]
                self.money -= price
                self.upgrades[buy] = level + 1
                self.event("bought", dict(upgrade=buy, level=level+1, price=price, money=self.money))
                reason = None
            if reason:
                self.event("buy_failed", dict(action=buy, reason=reason))
        if inp.pressed("shop_done") or self.shop_time == 0:
            self.event("shop_end", {"reason": "done" if inp.pressed("shop_done") else "time"})
            self.completed += 1
            if self.completed == self.days:
                self.done, self.reason = True, "days_complete"
            else:
                self.day += 1
                self.open_morning()

    def snapshot(self):
        state = self.sim.snapshot() if self.phase != "shop" else {"stock": self.sim.snapshot()["stock"]}
        state.update(type="snapshot", tick=self.tick, sim_tick=self.sim_tick, mode=self.mode, phase=self.phase,
                     phase_tick=self.phase_tick, state="finished" if self.done else "paused" if self.paused else "playing",
                     time_left_ticks=self.shop_time if self.phase == "shop" else self.sim.time_left_ticks,
                     money=self.money, earned=self.earned, reputation=self.reputation,
                     score=self.earned + self.tuning["score"]["reputation_multiplier"] * math.floor(self.reputation))
        if self.mode == "day":
            state.update(day=self.day, day_plan=self.plan, upgrades=dict(self.upgrades), active_upgrades=dict(self.active))
        return state


def run_campaign(mode, tuning, scenario, seed, frames, ticks, path, interval, days, inventory, inventory_out):
    game = Campaign(mode, tuning, scenario, seed, days, inventory)
    inputs = InputPlayer(frames, BUTTONS)
    buys = {f["tick"]: f["buy"] for f in frames if "buy" in f}
    writer = JsonlWriter(path)
    try:
        writer.write(game.snapshot())
        for row in game.events:
            writer.write(row)
        while game.tick < ticks and not game.done:
            previous = game.phase
            game.step(inputs.advance(game.tick), buys.get(game.tick))
            for row in game.events:
                writer.write(row)
            if game.done or game.tick == ticks or game.tick % interval == 0 or previous != game.phase:
                writer.write(game.snapshot())
        state = game.snapshot()
        end = {key: state[key] for key in ("sim_tick", "mode", "state", "money", "earned", "reputation", "score")}
        if mode == "day":
            end["days_completed"] = game.completed
        writer.write(dict(end, type="end", ticks=game.tick, reason=game.reason))
    finally:
        writer.close()
    if inventory_out and game.done:
        write_inventory(inventory_out, game.sim.inventory_items())
