"""Cửa sổ chơi trực tiếp bằng TRÌNH DUYỆT, chỉ dùng thư viện chuẩn Python.

    python3 -m chonoi.live --mode gather|quan [--seed N] [--port 8000]

Máy chủ HTTP nhỏ (ThreadingHTTPServer) phục vụ `chonoi/web/index.html` và hai API:
    GET  /state  -> snapshot JSON hiện tại (cùng trường như dòng snapshot của headless) + `meta` + `events`
    POST /input  -> {"move": [a, b], "interact": bool, "catch": bool}   (trạng thái phím đang giữ)
    POST /restart -> chơi lại từ đầu (cùng seed, cùng scenario)

Mô phỏng chạy 60 tick/s trong một luồng nền, dùng CÙNG lớp sim như headless (qua `runner.Session`).
Client chỉ ĐỌC snapshot và tự bỏ qua trường chưa có, nên luật do nhóm viết thêm trường nào cũng không vỡ.
Ngẫu nhiên vẫn đi qua `Streams` (seed); chỉ nhịp chạy theo đồng hồ thật, không đi vào luật.
"""

import argparse
import json
import os
import sys
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .contract import DEFAULT_PATH, LEGACY_PATH, load_contract
from .campaign import BUTTONS, Campaign
from .errors import BadInput
from .inputs import LiveInputs
from .inventory import read_inventory, write_inventory
from .runner import Session
from .scenario import load_scenario
from .sim.river_live import RiverFish

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
TICK_S = 1.0 / 60.0
MAX_BODY = 4096
RECENT_EVENTS = 40


class LiveGame:
    """Một lượt chơi + luồng nền bước 60 tick/s. Mọi truy cập trạng thái đi qua khóa."""

    def __init__(self, mode, tuning, scenario, seed, inventory=None, inventory_out=None):
        self.seed = seed
        self._args = ("gather" if mode == "day" else mode, tuning, scenario, seed, inventory)
        self.mode = mode
        self.tuning = tuning
        self.inventory_out = inventory_out
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None
        self._reset()

    def _reset(self):
        self.session = Session(*self._args)
        self.morning_result = None
        self.meals_paid = 0
        self.tips = 0
        self.river_fish = RiverFish(self.session.sim) if self.mode == "day" else None
        self.inputs = LiveInputs()
        self.events = []
        self._saved = False
        self.error = None

    # --- luồng nền ----------------------------------------------------------------
    def start(self):
        self._thread = threading.Thread(target=self._loop, name="chonoi-sim", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self):
        nxt = time.perf_counter()
        while not self._stop.is_set():
            nxt += TICK_S
            with self._lock:
                try:
                    self._tick_once()
                except Exception:  # luật của nhóm lỗi: báo ra terminal + client, dừng bước (restart để chơi lại)
                    self.error = traceback.format_exc()
                    sys.stderr.write(self.error)
                    self.session.sim.done = True
                    self.session.sim.reason = "error"
            delay = nxt - time.perf_counter()
            if delay > 0:
                self._stop.wait(delay)
            elif delay < -0.25:  # chạy chậm quá thì bỏ bù, tránh chạy dồn
                nxt = time.perf_counter()

    def _tick_once(self):
        s = self.session
        if s.done:
            return
        if self.river_fish is not None:
            self.river_fish.advance(s.sim)
        for row in s.step(self.inputs.advance()):
            self.events.append(row)
            if self.mode == "day" and row["name"] == "paid":
                self.meals_paid += 1
                self.tips += row["data"]["tip"]
        del self.events[:-RECENT_EVENTS]
        if self.mode == "day" and s.done and s.mode == "gather":
            items = s.sim.inventory_items()
            self.morning_result = {"reason": s.sim.reason, "items": items}
            self.river_fish = None
            self.session = Session("quan", self.tuning, {}, self.seed, inventory=items)
            self.inputs = LiveInputs()
            return
        if s.done and not self._saved:
            self._saved = True
            if self.inventory_out:
                try:
                    s.write_inventory_if_done(self.inventory_out)
                except OSError as e:
                    sys.stderr.write(f"lỗi ghi kho: {e}\n")

    # --- API cho handler -----------------------------------------------------------
    def state_json(self) -> bytes:
        with self._lock:
            snap = self.session.snapshot()
            snap["meta"] = self.tuning[self.session.mode]
            if self.mode == "day":
                snap["day"] = {"morning": self.morning_result, "meals_paid": self.meals_paid, "tips": self.tips}
            snap["events"] = list(self.events)
            snap["finished"] = self.session.done
            snap["reason"] = self.session.sim.reason if self.session.done else None
            snap["error"] = self.error
            return json.dumps(snap, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    buttons = ("interact", "catch")

    def set_input(self, body: dict):
        move = body.get("move")
        if move is not None:
            ok = (isinstance(move, list) and len(move) == 2 and
                  all(isinstance(c, (int, float)) and not isinstance(c, bool) and abs(c) <= 1 for c in move))
            if not ok:
                raise ValueError("move phải là [a, b] trong [-1, 1]")
        buttons = {}
        for b in self.buttons:
            if b in body:
                if not isinstance(body[b], bool):
                    raise ValueError(f"{b} phải là boolean")
                buttons[b] = body[b]
        with self._lock:
            self.inputs.set(move, **buttons)
            if "buy" in body and self.mode == "day" and isinstance(body["buy"], str):
                self.pending_buy = body["buy"]

    def restart(self):
        with self._lock:
            self._reset()


class CampaignLive(LiveGame):
    buttons = BUTTONS

    def __init__(self, mode, tuning, scenario, seed, inventory=None, inventory_out=None, days=5):
        self.campaign_args = (mode, tuning, scenario, seed, days, inventory)
        super().__init__(mode, tuning, scenario, seed, inventory, inventory_out)

    def _reset(self):
        self.session = Campaign(*self.campaign_args)
        self.inputs = LiveInputs(BUTTONS)
        self.events = list(self.session.events)
        self.screen = "menu" if self.mode == "day" else ""
        self.screen_ticks = 0
        self.shift = {"served": 0, "left": 0, "tips": 0}
        self.sales = {}
        self.tips = 0
        self.pending_buy = None
        self.error = None

    def _tick_once(self):
        game = self.session
        if game.done or self.error:
            return
        if self.screen:
            if self.screen == "intro":
                self.screen_ticks += 1
                if self.screen_ticks >= self.tuning["tick_hz"] * 4:
                    self.screen = ""
            return
        previous = game.phase
        game.step(self.inputs.advance(), self.pending_buy)
        self.pending_buy = None
        for row in game.events:
            if row["name"] == "served":
                self.shift["served"] += 1
                dish = row["data"]["dish_id"]
                self.sales[dish] = self.sales.get(dish, 0) + 1
            elif row["name"] == "paid":
                self.tips += row["data"]["tip"]
                self.shift["tips"] += row["data"]["tip"]
            elif row["name"] == "customer_left":
                self.shift["left"] += 1
        if game.phase != previous:
            self.screen = {"gather":"intro","quan":"evening","shop":"result"}[game.phase]
            self.screen_ticks = 0
            if game.phase == "gather":
                self.shift = {"served":0, "left":0, "tips":0}
        self.events.extend(game.events)
        del self.events[:-RECENT_EVENTS]
        if game.done and self.inventory_out:
            write_inventory(self.inventory_out, game.sim.inventory_items())

    def navigate(self, action):
        with self._lock:
            if action == "menu":
                self._reset()
            elif action == "exit" and self.screen == "menu":
                self.screen = "exit"
            elif action == "next":
                if self.screen in ("menu","exit"):
                    self.screen = "intro" if self.screen == "menu" else "menu"
                    self.screen_ticks = 0
                elif self.screen:
                    self.screen = ""
                elif self.session.paused:
                    self.inputs.set(pause=False)
                    self.inputs.set(pause=True)
                    self.inputs.set(pause=False)

    def state_json(self):
        with self._lock:
            game = self.session
            state = game.snapshot()
            if self.screen == "evening":
                available = game.sim._available()
                state["cookable"] = [k for k in sorted(game.plan["dishes"])
                                     if all(available[x] >= n for x, n in game.sim.menu[k]["recipe"].items())]
            state.update(meta=self.tuning[game.phase], events=self.events, finished=game.done,
                         error=self.error, reason=game.reason if game.done else None,
                         sales=self.sales, tips=self.tips, campaign=True, screen=self.screen, shift=self.shift)
            return json.dumps(state, ensure_ascii=False).encode()


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    game: LiveGame = None  # gán trên lớp con trong make_server

    def log_message(self, fmt, *args):  # yên lặng
        pass

    def _send(self, code, body: bytes, ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/state":
            self._send(200, self.game.state_json())
        elif path in ("/", "/index.html"):
            try:
                with open(os.path.join(WEB_DIR, "index.html"), "rb") as f:
                    self._send(200, f.read(), "text/html; charset=utf-8")
            except OSError:
                self._send(404, b'{"error":"thieu index.html"}')
        else:
            self._send(404, b'{"error":"khong co"}')

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if n < 0 or n > MAX_BODY:
            self._send(400, b'{"error":"body sai"}')
            return
        raw = self.rfile.read(n) if n else b""
        try:
            if path == "/input":
                body = json.loads(raw.decode("utf-8") or "{}")
                if not isinstance(body, dict):
                    raise ValueError("body phải là object")
                self.game.set_input(body)
            elif path == "/screen" and isinstance(self.game, CampaignLive):
                action = raw.decode()
                if action not in ("menu","exit","next"):
                    raise ValueError("thao tác màn hình sai")
                self.game.navigate(action)
            elif path == "/restart":
                self.game.restart()
            else:
                self._send(404, b'{"error":"khong co"}')
                return
        except (ValueError, UnicodeDecodeError) as e:
            self._send(400, json.dumps({"error": str(e)}).encode("utf-8"))
            return
        self._send(200, b'{"ok":true}')


class LiveServer:
    """Máy chủ + mô phỏng. port=0 -> cổng ngẫu nhiên (đọc `.port`)."""

    def __init__(self, game: LiveGame, host="127.0.0.1", port=8000):
        handler = type("Handler", (_Handler,), {"game": game})
        self.game = game
        self.httpd = ThreadingHTTPServer((host, port), handler)
        self.httpd.daemon_threads = True
        self.host = host
        self.port = self.httpd.server_address[1]
        self._thread = None

    @property
    def url(self):
        return f"http://{self.host}:{self.port}/"

    def start(self):
        self.game.start()
        self._thread = threading.Thread(target=self.httpd.serve_forever, name="chonoi-http", daemon=True)
        self._thread.start()

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        if self._thread:
            self._thread.join(timeout=2)
        self.game.stop()


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="chonoi.live", description="Chơi trực tiếp trên trình duyệt (starter).")
    p.add_argument("--mode", required=True, choices=["gather", "quan", "day"])
    p.add_argument("--rules", choices=["1.0", "1.2"], default="1.2")
    p.add_argument("--days", type=int, default=5)
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--port", type=int, default=8000, help="0 = cổng ngẫu nhiên")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--scenario")
    p.add_argument("--inventory", help="chỉ với quan: nạp kho từ file")
    p.add_argument("--inventory-out", dest="inventory_out", help="chỉ với gather: ghi kho khi kết thúc buổi")
    a = p.parse_args(argv)
    try:
        if a.inventory and a.mode != "quan":
            raise BadInput("--inventory chỉ dùng với quan")
        if a.inventory_out and a.mode != "gather":
            raise BadInput("--inventory-out chỉ dùng với gather")
        modern = a.rules == "1.2"
        if not 1 <= a.days <= 5:
            raise BadInput("số ngày phải từ 1 đến 5")
        tuning = load_contract(DEFAULT_PATH if modern else LEGACY_PATH)["tuning"]
        scenario = load_scenario(a.scenario, "gather" if a.mode == "day" and not modern else a.mode, tuning)
        inventory = read_inventory(a.inventory, individual=modern) if a.inventory else None
        if inventory is not None and "stock" in scenario:
            raise BadInput("vừa có quan.stock vừa có --inventory")
        if modern:
            game = CampaignLive(a.mode, tuning, scenario, a.seed, inventory, a.inventory_out, a.days)
        else:
            game = LiveGame(a.mode, tuning, scenario, a.seed, inventory, a.inventory_out)
        server = LiveServer(game, a.host, a.port)
    except BadInput as e:
        sys.stderr.write(f"đầu vào sai: {e}\n")
        return 2
    except OSError as e:
        sys.stderr.write(f"không mở được cổng {a.port}: {e}\n")
        return 1
    server.start()
    print(f"Mở trình duyệt tại {server.url}  (chế độ {a.mode}, seed {a.seed}). Ctrl+C để dừng.", flush=True)
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
