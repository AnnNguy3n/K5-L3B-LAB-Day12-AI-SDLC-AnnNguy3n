"""Kiểm lại lượt demo từ manifest, fixture và log đã lưu. Chạy từ gốc repo."""
import json
import shlex
import subprocess
import tempfile
from pathlib import Path


def main():
    manifest = json.loads(Path("game.contract.json").read_text())
    command = shlex.split(manifest["headless_cmd"])
    fixtures = Path("tests/fixtures/campaign")
    proof = Path("docs/proof/bo-sung/luot-choi.txt")
    with tempfile.TemporaryDirectory() as work:
        for seed in (1, 1):
            out = Path(work) / "day.jsonl"
            subprocess.run([*command, "--mode", "day", "--days", "1", "--seed", str(seed),
                            "--scenario", fixtures / "mot-ngay.json", "--inputs", fixtures / "thao-tac.json",
                            "--ticks", "2000", "--snapshot-every", "2000", "--out", out], check=True)
            if out.read_bytes() != proof.read_bytes():
                raise SystemExit("Log khác bằng chứng đã lưu.")
        rows = [json.loads(line) for line in out.read_text().splitlines()]
        for row in rows:
            if row.get("name") in ("fish_caught", "cook_started", "paid", "shop_end") or row["type"] == "end":
                print(json.dumps(row, ensure_ascii=False))
    print("Hai lượt trùng từng byte với log đã lưu.")


if __name__ == "__main__":
    main()
