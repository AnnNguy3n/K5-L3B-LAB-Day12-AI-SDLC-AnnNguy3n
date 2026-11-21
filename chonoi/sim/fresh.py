"""Vật phẩm được giữ theo id. Giá và ngưỡng dùng số thập phân trước khi xuất JSON."""
from collections import Counter
from decimal import Decimal, ROUND_FLOOR

from ..errors import BadInput
from ..ids import id_key, sort_by_id
from .gather import GatherSim
from .quan import QuanSim
from .encounters import Encounters
from .schools import Schools


class Pantry:
    def __init__(self, items, tuning, location):
        self.spec = tuning["freshness"]
        self.hz = tuning["tick_hz"]
        # Một đơn vị ứng với 1/(60*4) điểm tươi. Trừ theo tick bằng số nguyên.
        self.scale = self.hz * 4
        decay = self.spec["gather_decay_per_s" if location == "hold" else "quan_decay_per_s"]
        self.loss = Decimal(str(decay)) * 4
        self.limit = self.spec["spoiled_below"] * self.scale
        self.location = location
        self.data = {}
        kinds = {k for d in tuning["menu"].values() for k in d["recipe"]}
        if not isinstance(items, list):
            raise BadInput("kho v1.2 cần một mảng cá thể")
        for item in items:
            if not isinstance(item, dict) or set(item) != {"id", "kind", "fresh"}:
                raise BadInput("cá thể cần đúng id, kind, fresh")
            key, kind, fresh = item["id"], item["kind"], item["fresh"]
            if not isinstance(key, str) or not key or key in self.data or not isinstance(kind, str) or kind not in kinds:
                raise BadInput("id trùng, id trống hoặc nguyên liệu lạ")
            if type(fresh) not in (float, int) or not 0 <= fresh <= self.spec["initial"]:
                raise BadInput("độ tươi ngoài miền")
            self.data[key] = (kind, Decimal(str(fresh)) * self.scale)

    def public(self, keys):
        return [{"id": key, "kind": self.data[key][0], "fresh": float(self.data[key][1] / self.scale)}
                for key in keys]

    def age(self, events):
        for key in sorted(self.data, key=id_key):
            kind, before = self.data[key]
            after = max(0, before - self.loss)
            self.data[key] = kind, after
            if before >= self.limit > after:
                events.append(("spoiled", {"item_id": key, "kind": kind, "location": self.location}))


class FreshGather(GatherSim):
    def __init__(self, tuning, scenario, streams, ids, day=1):
        super().__init__(tuning, dict(scenario, hold=[], fish=scenario.get("fish", [])), streams, ids)
        self.schools = Schools(self, self.t, scenario)
        self.encounters = Encounters(self, scenario, day)
        for fish, source in zip(self.fish, scenario.get("fish", [])):
            fish["age_ticks"] = source.get("age_ticks", 0)
        self.pantry = Pantry(scenario.get("hold", []), tuning, "hold")
        self.hold = list(self.pantry.data)
        for key in self.hold:
            ids.reserve(key)

    def _encounters(self, events):
        self.encounters.advance(self, events)

    def _age_hold(self, events):
        self.pantry.age(events)

    def _add_items(self, kind, quantity):
        for _ in range(quantity):
            key = self.ids.new("I")
            self.hold.append(key)
            self.pantry.data[key] = (kind, Decimal(self.pantry.spec["initial"] * self.pantry.scale))

    def inventory_items(self):
        return self.pantry.public(sorted(self.hold, key=id_key))

    def snapshot(self):
        return dict(super().snapshot(), hold=self.pantry.public(self.hold), fish=sort_by_id(self.fish),
                    monsters=self.encounters.monsters)

    def step(self, inp):
        events = super().step(inp)
        if not self.done:
            self.schools.step(self, events)
        for name, data in events:
            if name == "faint":
                data["lost"] = self.pantry.public(data["lost"])
        return events


class FreshQuan(QuanSim):
    def __init__(self, tuning, scenario, streams, ids, inventory=None):
        self.pantry = Pantry(scenario.get("stock", []) if inventory is None else inventory, tuning, "stock")
        super().__init__(tuning, dict(scenario, stock={}), streams, ids)

    def snapshot(self):
        return dict(super().snapshot(), stock=self.pantry.public(sorted(self.pantry.data, key=id_key)))

    def _free(self):
        used = {key for c in self.customers for key in c["reserved"]}
        return {key: value for key, value in self.pantry.data.items()
                if value[1] >= self.pantry.limit and key not in used}

    def _available(self):
        return Counter(kind for kind, fresh in self._free().values())

    def _choose(self, recipe):
        free = self._free()
        chosen = []
        for kind, count in sorted(recipe.items()):
            keys = sorted((key for key in free if free[key][0] == kind),
                          key=lambda key: (-free[key][1], id_key(key)))
            if len(keys) < count:
                return []
            chosen.extend(keys[:count])
        return chosen

    def _reserve_customer(self, c, status):
        recipe = self.menu[c["dish_id"]]["recipe"] if status == "reserved" else {}
        keys = c.setdefault("reserved", self._choose(recipe))
        free = self._free()
        if not isinstance(keys, list) or any(not isinstance(k, str) or k not in free for k in keys):
            raise BadInput("phần giữ chứa id không khả dụng")
        if len(set(keys)) != len(keys) or Counter(free[k][0] for k in keys) != recipe:
            raise BadInput("phần giữ không đủ công thức")

    def _age_stock(self, events):
        self.pantry.age(events)
        spoiled = {d["item_id"] for name, d in events if name == "spoiled"}
        for c in sorted(self.customers, key=lambda c: (c["order_tick"], id_key(c["table_id"]))):
            if spoiled.intersection(c["reserved"]):
                c["reserved"] = []
                c["reserved"] = self._choose(self.menu[c["dish_id"]]["recipe"])
                if not c["reserved"]:
                    c["order_status"] = "unfulfillable"

    def _consume(self, c):
        keys = sorted(c["reserved"], key=lambda k: (self.pantry.data[k][0], id_key(k)))
        items = self.pantry.public(keys)
        total = sum(self.pantry.data.pop(k)[1] for k in keys)
        price = self.menu[c["dish_id"]]["price"] * total / (len(keys) * self.pantry.spec["initial"] * self.pantry.scale)
        c["reserved"] = []
        return items, int(price.to_integral_value(rounding=ROUND_FLOOR))
