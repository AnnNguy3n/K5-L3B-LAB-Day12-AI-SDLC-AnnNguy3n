"""Chạy liên tục nhiều ngày bằng input của bot trong cùng một Campaign."""
import argparse
import json
import math
import sys
import time
from pathlib import Path

from .campaign import Campaign
from .contract import DEFAULT_PATH, load_contract
from .inputs import LiveInputs


def action(game):
    sim = game.sim
    if game.phase == "shop":
        return [0, 0], False, True
    if game.phase == "gather":
        nodes = [n for n in sim.nodes if n["kind"] == "bong_sung" and not n["regrow_ticks"]]
        target = sim.t["dock_pos"]
        if len(sim.hold) < 2 and nodes:
            target = min(nodes, key=lambda n: math.dist(sim.pos, n["pos"]))["pos"]
    elif sim.hand:
        order = next(c for c in sim.customers if c["id"] == sim.hand["order_id"])
        target = next(t["pos"] for t in sim.tables if t["id"] == order["table_id"])
    else:
        target = sim.stoves[0]["pos"]
    dx, dy = (b-a for a, b in zip(sim.pos, target))
    length = math.hypot(dx, dy)
    if length > sim.t["interact_radius"] / 2:
        return [dx/length, dy/length], False, False
    return [0, 0], game.tick % 2 == 0, False


def run(seed, days):
    start = time.monotonic()
    results = []
    report = {"seed": seed, "days": days, "days_completed": 0, "crashes": 0, "results": results}
    try:
        tuning = load_contract(DEFAULT_PATH)["tuning"]
        game = Campaign("day", tuning, {}, seed, days)
        inputs = LiveInputs(("interact", "shop_done"))
        harvested = paid = 0
        while not game.done:
            if game.phase == "shop":
                last = game.snapshot()
            move, interact, finish = action(game)
            inputs.set(move, interact=interact, shop_done=finish)
            game.step(inputs.advance())
            for row in game.events:
                if row["name"] == "gather_end":
                    harvested = len(row["data"]["inventory"]["items"])
                elif row["name"] == "paid":
                    paid += 1
                elif row["name"] == "shop_end":
                    results.append(dict(day=row["day"], earned=last["earned"], reputation=last["reputation"],
                                        score=last["score"], harvested=harvested, paid_orders=paid))
                    report["days_completed"] += 1
                    harvested = paid = 0
    except Exception as error:
        report.update(crashes=1, error=f"{type(error).__name__}: {error}")
    report["duration_s"] = round(time.monotonic() - start, 3)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--days", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.days < 1:
        parser.error("--days phải dương")
    report = run(args.seed, args.days)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    if report["crashes"]:
        print(report["error"], file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
