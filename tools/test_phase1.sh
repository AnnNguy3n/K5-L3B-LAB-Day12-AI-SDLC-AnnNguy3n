#!/bin/sh
# Chạy cả test starter và test luật Phase 1 từ thư mục gốc.
set -eu
PYTHONPATH=tests:. exec python3 -m unittest discover -s tests -v
