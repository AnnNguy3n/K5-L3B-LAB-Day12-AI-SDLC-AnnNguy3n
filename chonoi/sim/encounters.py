"""Tuần tra, đuổi và lùi sau va chạm trong mặt cắt của sông."""
import math
from ..ids import sort_by_id
from ..errors import BadInput


def direction(a, b):
    dist = math.dist(a, b)
    if dist == 0:
        return [1, 0]
    return [(b[i] - a[i]) / dist for i in (0, 1)]


class Encounters:
    def __init__(self, sim, scenario, day):
        self.spec = sim.t["monsters"]
        spawns = [m for m in self.spec["spawns"] if m["from_day"] <= day]
        self.monsters = []
        for m in sort_by_id(scenario.get("monsters", spawns)):
            entity = dict(m, pos=list(m["pos"]))
            entity.pop("from_day", None)
            entity.setdefault("target_idx", 1)
            entity.setdefault("state", "patrol")
            entity.setdefault("state_ticks_left", 0)
            entity.setdefault("recoil_dir", None)
            if entity["kind"] not in self.spec["species"] or entity["target_idx"] not in (0, 1):
                raise BadInput("loài hoặc đích tuần tra sai")
            self.monsters.append(entity)

    def advance(self, sim, events):
        hits = []
        for m in self.monsters:
            t = self.spec["species"][m["kind"]]
            pos = m["pos"]
            dist = math.dist(pos, sim.pos)
            if m["state"] == "recoil":
                vec = m["recoil_dir"]
                step = t["recoil_dist"] / t["recoil_ticks"]
                m["state_ticks_left"] -= 1
                if not m["state_ticks_left"]:
                    m.update(state="patrol", recoil_dir=None)
                eligible = False
            else:
                eligible = sim.pos[1] >= t["depths"][0]
                if not eligible or dist > t["exit_radius"]:
                    m["state"] = "patrol"
                elif dist <= t["detect_radius"]:
                    m["state"] = "chase"
                chase = m["state"] == "chase"
                target = sim.pos if chase else m["waypoints"][m["target_idx"]]
                vec = direction(pos, target)
                step = min(math.dist(pos, target), t["chase_speed" if chase else "patrol_speed"] / sim.hz)
                if not chase and step >= math.dist(pos, target):
                    m["target_idx"] = 1 - m["target_idx"]
            for i, (lo, hi) in enumerate((sim.t["bounds"]["x"], t["depths"])):
                pos[i] = min(hi, max(lo, pos[i] + vec[i] * step))
            if eligible and not sim.invuln_ticks and math.dist(pos, sim.pos) <= t["hit_radius"]:
                hits.append(m)
        if not hits:
            return
        m = min(hits, key=lambda m: math.dist(m["pos"], sim.pos))
        m.update(state="recoil", recoil_dir=direction(sim.pos, m["pos"]),
                 state_ticks_left=self.spec["species"][m["kind"]]["recoil_ticks"])
        sim.invuln_ticks = self.spec["invuln_ticks"]
        sim.hp -= 1
        count = math.floor(len(sim.hold) * self.spec["loss_ratio"])
        lost = [sim.hold.pop() for _ in range(count)]
        events.append(("monster_hit", {"monster_id": m["id"], "hp": sim.hp, "pos": list(sim.pos),
                                       "lost": sim.pantry.public(lost)}))
        for key in lost:
            del sim.pantry.data[key]
        if sim.hp == 0:
            events.append(("faint", {"cause": "monster", "hp": 0, "lost": sim.hold[::-1]}))
            sim.hold.clear()
            sim._finish("fainted", events)
