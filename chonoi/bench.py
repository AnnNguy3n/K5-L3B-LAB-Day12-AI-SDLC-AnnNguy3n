"""Đếm frame đã vẽ của game trong Chrome/Chromium tại viewport 1280×720."""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from .contract import DEFAULT_PATH, load_contract
from .live import CampaignLive, LiveServer, _Handler


PAGE = """<!doctype html><meta charset=utf-8><style>*{margin:0;border:0}</style>
<iframe width=1280 height=720 src="/" title="Quán ăn chợ nổi"></iframe>
<script>
const scene = document.querySelector("iframe");
let first, previous, firstTick, sent = false;
const intervals = [];
scene.onload = () => {
  scene.contentWindow.onGameFrame = (tick, width, height) => {
    const now = performance.now();
    if (first === undefined) { first = previous = now; firstTick = tick; return; }
    if (sent) return;
    intervals.push(now - previous);
    previous = now;
    if (now - first >= DURATION * 1000) {
      sent = true;
      intervals.sort((a,b) => a-b);
      fetch("/measurement", {method:"POST", body:JSON.stringify({
        frames:intervals.length, elapsed_ms:now-first, width, height, first_tick:firstTick, last_tick:tick,
        p95_frame_ms:intervals[Math.ceil(intervals.length * .95)-1], browser:navigator.userAgent
      })});
    }
  };
};
</script>"""


def measure(seed, duration, executable):
    game = CampaignLive("gather", load_contract(DEFAULT_PATH)["tuning"], {}, seed)
    result = {}
    received = threading.Event()

    class BenchHandler(_Handler):
        def do_GET(self):
            if self.path == "/measure":
                self._send(200, PAGE.replace("DURATION", str(duration)).encode(), "text/html; charset=utf-8")
            else:
                super().do_GET()

        def do_POST(self):
            if self.path != "/measurement":
                return super().do_POST()
            try:
                size = int(self.headers["Content-Length"])
                if not 0 < size <= 4096:
                    raise ValueError()
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise ValueError()
            except (ValueError, TypeError):
                self._send(400, b"{}")
                return
            result.update(data)
            self._send(200, b"{}")
            received.set()

    server = LiveServer(game, port=0, handler_class=BenchHandler)
    server.start()
    try:
        with tempfile.TemporaryDirectory() as profile:
            args = [executable, "--headless", "--no-first-run", "--disable-extensions",
                    "--disable-background-networking", "--force-device-scale-factor=1",
                    "--window-size=1320,850", "--user-data-dir=" + profile, server.url + "measure"]
            proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                if not received.wait(duration + 15):
                    raise RuntimeError("trình duyệt chưa trả kết quả đo")
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
    finally:
        server.stop()
    if ((result["width"], result["height"]) != (1280, 720) or result["frames"] <= 0
            or result["last_tick"] <= result["first_tick"] or result["elapsed_ms"] < duration * 1000):
        raise RuntimeError("kích thước, thời gian hoặc tiến độ mô phỏng không đạt điều kiện đo")
    result.update(seed=seed, duration_s=duration, avg_fps=round(result["frames"] * 1000 / result["elapsed_ms"], 2))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not math.isfinite(args.duration) or args.duration <= 0:
        parser.error("thời lượng phải hữu hạn và dương")
    candidates = [os.getenv("CHROME_BIN"), "google-chrome", "chromium", "chromium-browser",
                  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    executable = next((shutil.which(c) for c in candidates if c and shutil.which(c)), None)
    if not executable:
        parser.error("cần Chrome/Chromium hoặc đường dẫn CHROME_BIN")
    try:
        result = measure(args.seed, args.duration, executable)
        args.out.write_text(json.dumps(result, indent=2) + "\n")
    except (RuntimeError, OSError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
