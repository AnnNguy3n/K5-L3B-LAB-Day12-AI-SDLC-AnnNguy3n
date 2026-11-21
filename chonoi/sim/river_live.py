"""Đàn cá chuyển động trong lượt chơi day trên trình duyệt."""
import json
from pathlib import Path

from ..ids import sort_by_id


class RiverFish:
    def __init__(self, sim):
        data = json.loads(Path(__file__).with_name("river_live.json").read_text())
        self.step_size = data["swim_speed"] / sim.hz
        self.interval = round(data["spawn_interval_s"] * sim.hz)
        self.min_depth = max(data["spawn_min_depth"], sim.t["surface_depth"] + self.step_size)
        self.limit = len(sim.fish)
        self.elapsed = 0
        self.stream = sim.rng.get("live_river_fish")

    def advance(self, sim):
        self.elapsed += 1
        left, right = sim.t["bounds"]["x"]
        for fish in sort_by_id(sim.fish):
            # Đàn đi ngang. Đổi chiều ở mép và giữ phần quãng đường còn lại.
            direction = -1 if 90 < fish["heading_deg"] % 360 < 270 else 1
            x = fish["pos"][0] + direction * self.step_size
            if x >= right:
                x, direction = 2 * right - x, -1
            elif x <= left:
                x, direction = 2 * left - x, 1
            fish["pos"][0] = x
            fish["heading_deg"] = 0 if direction == 1 else 180

        if self.elapsed % self.interval or len(sim.fish) >= self.limit:
            return
        kind = self.stream.choice(sorted(sim.t["fish_yield"]))
        fish = {"id": sim.ids.new("F"), "kind": kind,
                "pos": [self.stream.uniform(left, right),
                        self.stream.uniform(self.min_depth, sim.t["bounds"]["d"][1])],
                "heading_deg": self.stream.choice([0, 180])}
        sim.fish.append(fish)
