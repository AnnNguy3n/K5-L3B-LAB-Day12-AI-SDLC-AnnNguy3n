"""Chuyển động và lịch sinh đàn cho các ngày theo TICKET-02."""
import math
from ..ids import sort_by_id


class Schools:
    def __init__(self, sim, spec, scenario):
        self.spec = spec
        self.enabled = scenario.get("random_fish", True)
        self.rng = sim.rng.get("schools")
        self.age = 0
        if self.enabled and "fish" not in scenario:
            sim.fish.clear()
            for _ in range(spec["fish_initial"]):
                self.spawn(sim)
        for fish in sim.fish:
            fish.setdefault("age_ticks", 0)

    def spawn(self, sim):
        spec = self.spec
        locations = {}
        for kind, depths in spec["fish_spawn_depths"].items():
            locations[kind] = [[x, d] for x in spec["fish_spawn_x"] for d in depths
                               if all(math.dist([x, d], f["pos"]) > spec["fish_spawn_clearance"] for f in sim.fish)]
        kinds = sorted(k for k in locations if locations[k])
        if not kinds:
            return None
        kind = self.rng.choices(kinds, [spec["fish_weights"][k] for k in kinds])[0]
        f = {"id": sim.ids.new("F"), "kind": kind, "pos": self.rng.choice(locations[kind]),
             "heading_deg": self.rng.randrange(360), "age_ticks": 0}
        sim.fish.append(f)
        return f

    def step(self, sim, events):
        if not self.enabled:
            return
        self.age += 1
        for f in sort_by_id(sim.fish):
            f["age_ticks"] += 1
            if f["age_ticks"] % self.spec["fish_turn_ticks"] == 0:
                f["heading_deg"] = self.rng.randrange(360)
            rad = math.radians(f["heading_deg"])
            direction = [math.cos(rad), math.sin(rad)]
            for i, (lo, hi) in enumerate((self.spec["fish_x"], self.spec["fish_depths"][f["kind"]])):
                x = f["pos"][i] + direction[i] * self.spec["fish_speed"] / sim.hz
                if x <= lo or x >= hi:
                    x = 2 * (lo if x <= lo else hi) - x
                    direction[i] *= -1
                f["pos"][i] = x
            f["heading_deg"] = math.degrees(math.atan2(direction[1], direction[0])) % 360
        if self.age % self.spec["fish_spawn_ticks"] == 0 and len(sim.fish) < self.spec["fish_max"]:
            fish = self.spawn(sim)
            if fish:
                events.append(("fish_spawned", {k: fish[k] for k in ("id", "kind", "pos")}))
