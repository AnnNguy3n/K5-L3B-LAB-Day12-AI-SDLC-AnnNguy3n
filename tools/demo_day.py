"""Chạy: python3 -m tools.demo_day. In biên bản của một lượt live theo tick."""
import json

from chonoi.contract import load_contract
from chonoi.live import LiveGame


def play():
    game = LiveGame("day", load_contract()["tuning"], {
        "player": {"pos": [6, 2]}, "fish": [{"id": "F1", "kind": "ca_loc", "pos": [6, 2]}]}, 1)
    inputs = {
        "gather": {0: {"catch": True, "move": [-1, -1]}, 67: {"interact": True, "move": [0, 0]}},
        "quan": {0: {"move": [-1, 0.5]}, 102: {"move": [0, 0]}, 120: {"interact": True},
                 121: {"interact": False}, 481: {"interact": True},
                 482: {"interact": False, "move": [1, -1]}, 615: {"interact": True, "move": [0, 0]}}
    }
    while not game.session.done:
        session = game.session
        action = inputs[session.mode].get(session.tick)
        if action:
            game.set_input(action)
        game._tick_once()
    return game


if __name__ == "__main__":
    state = json.loads(play().state_json())
    print(json.dumps({k: state[k] for k in ("day", "finished", "earned", "reputation", "score")},
                     indent=2, ensure_ascii=False))
