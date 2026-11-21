"""Mô phỏng ca tối: nhận đơn, nấu, bưng món và thanh toán."""

import math
from collections import Counter

from ..errors import BadInput
from ..ids import sort_by_id
from .ramp import ramp_velocity


class QuanSim:
    mode = "quan"
    phase = "quan"

    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        t = tuning["quan"]
        self.t = t
        self.menu = tuning["menu"]
        self.hz = tuning["tick_hz"]
        self.tick = 0
        self.random_customers = scenario.get("random_customers", True)
        self.rng = streams
        self.ids = ids
        p = scenario.get("player", {})
        self.pos = list(p.get("pos", t["start_pos"]))
        self.vel = [float(c) for c in p.get("vel", [0.0, 0.0])]
        self._tgt = None
        self._ramp_left = 0
        # kho: --inventory HOẶC scenario.stock (cả hai -> cli đã báo mã 2)
        self.stock = dict(inventory if inventory is not None else scenario.get("stock", {}))
        self.hand = scenario.get("hand")
        self.time_left_ticks = scenario.get("time_left_ticks", int(round(t["duration_s"] * self.hz)))
        self.reputation = scenario.get("reputation", t["reputation_initial"])
        self.stoves = [dict(s, state=s.get("state", "idle"), dish=s.get("dish"),
                            cook_ticks_left=s.get("cook_ticks_left", 0), ready_ticks=s.get("ready_ticks", 0))
                       for s in self._merge(t["stoves"], scenario.get("stoves", []))]
        self.tables = self._merge(t["tables"], scenario.get("tables", []))
        self.customers = []
        for entry in sort_by_id(scenario.get("customers", [])):
            customer = dict(entry)
            self._prepare_customer(customer)
            self.customers.append(customer)
            ids.reserve(customer["id"])
        self._validate_start()
        self.money = 0
        self.earned = 0
        self.shift_earned = 0
        self.done = False
        self.reason = None

    @staticmethod
    def _merge(defaults, updates):
        by_id = {d["id"]: dict(d) for d in defaults}
        for u in updates:
            if u["id"] not in by_id:
                raise BadInput(f"id bếp/bàn không tồn tại: {u['id']}")
            by_id[u["id"]].update(u)
        return sort_by_id(list(by_id.values()))

    def snapshot(self) -> dict:
        occupied = {c["table_id"]: c["id"] for c in self.customers}
        return {
            "player": {"pos": self.pos},
            "stock": {k: self.stock[k] for k in sorted(self.stock) if self.stock[k] > 0},
            "hand": self.hand,
            "stoves": [{k: s.get(k) for k in ("id", "pos", "state", "dish", "cook_ticks_left", "ready_ticks")}
                       for s in self.stoves],
            "tables": [{"id": tb["id"], "pos": tb["pos"], "customer_id": occupied.get(tb["id"])} for tb in self.tables],
            "customers": sort_by_id(self.customers),
        }

    def step(self, inp):
        events = []
        self.time_left_ticks = max(0, self.time_left_ticks - 1)
        self.tick += 1
        self._advance_kitchen(events)
        self._advance_customers(events)
        self._move(inp)
        if inp.pressed("interact"):
            self._interact(events)
        elapsed = self.tick - self.t["first_customer_tick"]
        if self.random_customers and elapsed >= 0 and elapsed % self._ticks("customer_interval_s") == 0:
            self._arrive(events)
        if self.time_left_ticks <= 0:
            self.done = True
            self.reason = "time"
            events.append(("quan_end", {"reason": "time", "money": self.money, "earned": self.earned,
                                        "shift_earned": self.shift_earned, "reputation": self.reputation}))
        return events

    def _ticks(self, name):
        return round(self.t[name] * self.hz)

    def _prepare_customer(self, c):
        dish = c.get("dish_id")
        if not isinstance(dish, str) or dish not in self.menu:
            raise BadInput("khách cần dish_id trong menu")
        state = c.setdefault("state", "waiting")
        if state not in ("waiting", "assigned", "eating"):
            raise BadInput("trạng thái khách không hợp lệ")
        recipe = self.menu[dish]["recipe"] if state == "waiting" else {}
        if c.setdefault("reserved", dict(recipe)) != recipe:
            raise BadInput("nguyên liệu giữ chỗ không khớp với đơn")
        c.setdefault("patience_ticks_left", self._ticks("patience_s"))
        if state == "eating" and not {"price", "tip", "eat_ticks_left"} <= c.keys():
            raise BadInput("khách đang ăn cần giá, tiền boa và thời gian ăn")
        for key in ("patience_ticks_left", "eat_ticks_left", "price", "tip"):
            if key in c and (type(c[key]) is not int or c[key] < 0):
                raise BadInput(f"{key} phải là số nguyên không âm")

    def _available(self):
        available = Counter(self.stock)
        for c in self.customers:
            available.subtract(c["reserved"])
        return available

    def _validate_start(self):
        if type(self.random_customers) is not bool:
            raise BadInput("random_customers phải là boolean")
        if type(self.reputation) not in (float, int) or not (
                self.t["reputation_min"] <= self.reputation <= self.t["reputation_max"]):
            raise BadInput("uy tín ngoài giới hạn")
        if any(v < 0 for v in self._available().values()):
            raise BadInput("giữ chỗ vượt số lượng trong kho")
        dishes = []
        if self.hand is not None:
            dishes.append(self.hand)
        for stove in self.stoves:
            state = stove["state"]
            if state not in ("idle", "cooking", "ready"):
                raise BadInput("trạng thái bếp không hợp lệ")
            for key in ("cook_ticks_left", "ready_ticks"):
                if type(stove[key]) is not int or stove[key] < 0:
                    raise BadInput(f"{key} phải là số nguyên không âm")
            if (state == "cooking") != (stove["cook_ticks_left"] > 0):
                raise BadInput("thời gian nấu không khớp trạng thái bếp")
            if state != "idle":
                dishes.append(stove["dish"])
            elif stove["dish"] is not None:
                raise BadInput("bếp trống còn món")
        if any(not isinstance(dish, str) or dish not in self.menu for dish in dishes):
            raise BadInput("món ở bếp hoặc trên tay không có trong menu")
        assigned = Counter(c["dish_id"] for c in self.customers if c["state"] == "assigned")
        if assigned != Counter(dishes):
            raise BadInput("mỗi đơn assigned cần đúng một món tại bếp hoặc trên tay")

    def _arrive(self, events):
        occupied = {c["table_id"] for c in self.customers}
        table = next((t for t in self.tables if t["id"] not in occupied), None)
        if table is None:
            return
        available = self._available()
        options = [dish for dish, spec in sorted(self.menu.items())
                   if all(available[k] >= count for k, count in spec["recipe"].items())]
        if not options:
            events.append(("no_dish", {"table_id": table["id"]}))
            return
        dish = self.rng.get("customer_order").choice(options)
        c = {"id": self.ids.new("C"), "table_id": table["id"], "dish_id": dish}
        self._prepare_customer(c)
        self.customers.append(c)
        events.append(("customer_arrived", {"customer_id": c["id"], "table_id": table["id"], "dish_id": dish}))

    def _advance_kitchen(self, events):
        for stove in self.stoves:
            if stove["state"] == "ready":
                stove["ready_ticks"] += 1
            elif stove["state"] == "cooking":
                stove["cook_ticks_left"] -= 1
                if stove["cook_ticks_left"] == 0:
                    stove["state"] = "ready"
                    events.append(("dish_ready", {"stove_id": stove["id"], "dish_id": stove["dish"]}))

    def _advance_customers(self, events):
        for c in sort_by_id(self.customers):
            if c["state"] == "eating":
                c["eat_ticks_left"] = max(0, c["eat_ticks_left"] - 1)
                if c["eat_ticks_left"] == 0:
                    total = c["price"] + c["tip"]
                    self.money += total
                    self.earned += total
                    self.shift_earned += total
                    if c["tip"]:
                        self._reputation(self.t["tip_reputation"])
                    events.append(("paid", {"customer_id": c["id"], "price": c["price"], "tip": c["tip"]}))
                    self.customers.remove(c)
            else:
                c["patience_ticks_left"] = max(0, c["patience_ticks_left"] - 1)
                if c["patience_ticks_left"] == 0:
                    if c["state"] == "assigned":
                        self._discard_order(c["dish_id"])
                    self.customers.remove(c)
                    self._reputation(self.t["left_reputation_delta"])
                    events.append(("customer_left", {"customer_id": c["id"], "reason": "patience"}))

    def _discard_order(self, dish):
        if self.hand == dish:
            self.hand = None
            return
        for stove in self.stoves:
            if stove["dish"] == dish:
                self._clear_stove(stove)
                return

    @staticmethod
    def _clear_stove(stove):
        stove.update(state="idle", dish=None, cook_ticks_left=0, ready_ticks=0)

    def _reputation(self, delta):
        self.reputation = max(self.t["reputation_min"], min(self.t["reputation_max"], self.reputation + delta))

    def _interact(self, events):
        # Cùng khoảng cách: bếp trước bàn, sau đó là thứ tự id.
        targets = [(s, True) for s in self.stoves] + [(t, False) for t in self.tables]
        target, is_stove = min(targets, key=lambda item: math.dist(self.pos, item[0]["pos"]))
        if math.dist(self.pos, target["pos"]) > self.t["interact_radius"]:
            return
        if is_stove:
            self._use_stove(target, events)
            return
        for c in self.customers:
            if c["table_id"] == target["id"] and c["state"] == "assigned" and self.hand == c["dish_id"]:
                price = self.menu[self.hand]["price"]
                fast = c["patience_ticks_left"] >= self._ticks("patience_s") * self.t["tip_min_patience_ratio"]
                c.update(state="eating", eat_ticks_left=self._ticks("eat_s"), price=price,
                         tip=round(price * self.t["tip_rate"]) if fast else 0)
                self.hand = None
                events.append(("served", {"customer_id": c["id"], "dish_id": c["dish_id"]}))
                return

    def _use_stove(self, stove, events):
        if self.hand is not None:
            return
        if stove["state"] == "ready":
            self.hand = stove["dish"]
            self._clear_stove(stove)
            events.append(("dish_picked", {"stove_id": stove["id"], "dish_id": self.hand}))
        elif stove["state"] == "idle":
            c = next((c for c in sort_by_id(self.customers) if c["state"] == "waiting"), None)
            if c is None:
                return
            for k, count in c["reserved"].items():
                self.stock[k] -= count
            dish = c["dish_id"]
            c.update(state="assigned", reserved={})
            stove.update(state="cooking", dish=dish, cook_ticks_left=round(self.menu[dish]["cook_s"] * self.hz))
            events.append(("cook_started", {"customer_id": c["id"], "dish_id": dish, "stove_id": stove["id"]}))

    def _move(self, inp):
        speed = self.t["walk_speed"]
        mx, mz = inp.move
        self.vel = ramp_velocity(self, (mx * speed, mz * speed), self.t["ramp_max_ticks"])
        b = self.t["bounds"]
        for i, axis in enumerate(("x", "z")):
            self.pos[i] += self.vel[i] / self.hz
            lo, hi = b[axis]
            if self.pos[i] <= lo:
                self.pos[i], self.vel[i] = lo, max(0.0, self.vel[i])
            elif self.pos[i] >= hi:
                self.pos[i], self.vel[i] = hi, min(0.0, self.vel[i])
