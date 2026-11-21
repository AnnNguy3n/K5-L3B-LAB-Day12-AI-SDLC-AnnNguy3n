#!/bin/sh
# Chạy từ thư mục gốc. Mỗi lần chạy ghi vào một thư mục mới.
set -eu
out=$(mktemp -d)
fixtures=tests/fixtures/phase-1
python3 -m chonoi.headless --rules 1.0 --mode gather --seed 1 --ticks 100 --scenario "$fixtures/gather.json" --inputs "$fixtures/gather-inputs.json" --snapshot-every 2000 --inventory-out "$out/kho.json" --out "$out/gather.jsonl"
python3 -m chonoi.headless --rules 1.0 --mode quan --seed 1 --ticks 1300 --scenario "$fixtures/quan.json" --inputs "$fixtures/quan-inputs.json" --snapshot-every 2000 --inventory "$out/kho.json" --out "$out/quan.jsonl"
echo "$out"
