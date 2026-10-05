#!/usr/bin/env bash
# Download CAP U.S. Reports volume zips 1-572 (CC0) into data/raw/cap_us with
# 4 parallel workers; resumable (finished volumes are skipped).
set -u
mkdir -p "$(dirname "$0")/data/raw/cap_us"
cd "$(dirname "$0")/data/raw/cap_us"
seq 1 572 | xargs -P 4 -I{} sh -c '[ -s {}.zip ] || curl -sS --retry 4 --retry-delay 2 --max-time 600 -o {}.zip.part https://static.case.law/us/{}.zip && mv {}.zip.part {}.zip'
ls *.zip | wc -l
