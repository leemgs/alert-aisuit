#!/usr/bin/env python3
"""Parse the CONAN "Table of Supreme Court Decisions Overruled by Subsequent
Decisions" from `pdftotext -layout` output into one row per (overruling,
overruled) pair.

Input:  the table region of GPO-CONAN-2022 (data/raw/overruled_table.txt)
Output: data/pairs_raw.csv with columns
        overruling_name, overruling_year, overruling_cite,
        overruled_name, overruled_year, overruled_cite, partial

`*_cite` is the official U.S. Reports cite "V U.S. P" (nominative reporter
removed) or "" when the table gives only a docket number (recent cases).
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

HEADER = re.compile(r"Overruling\s+Overruling\s+Overruled\s+Overruled")
YEAR = re.compile(r"^(1[789]\d\d|20\d\d)$")
US_CITE = re.compile(r"(\d+)\s+U\.\s?S\.\s+(?:\([^)]*\)\s+)?(\d+)")
SEG = re.compile(r"\S+(?: \S+)*")  # runs separated by 2+ spaces


def segments(line: str):
    return [(m.start(), m.group(0)) for m in SEG.finditer(line)]


def column_bounds(header_line: str) -> list[int]:
    return [m.start() for m in re.finditer(r"Overrul\w+", header_line)]


def us_cite(text: str) -> str:
    m = US_CITE.search(text)
    return f"{m.group(1)} U.S. {m.group(2)}" if m else ""


def case_name(text: str) -> str:
    m = re.search(r"\d+\s+U\.\s?S\.|No\.\s", text)
    name = text[: m.start()] if m else text
    return re.sub(r"\s+", " ", name).strip().rstrip(",;").strip()


def parse(lines: list[str]) -> list[dict]:
    bounds = None
    entries: list[dict] = []
    cur = None
    for line in lines:
        if HEADER.search(line):
            bounds = column_bounds(line)
            continue
        if bounds is None or len(bounds) < 4 or not line.strip():
            continue
        if re.search(r"^\s*\d{4}\s*$|TABLE OF|continues|Decision\(?s?\)?\s*$|^\s*Year", line):
            continue
        # Header words are centred over their columns, so use the two year
        # columns as anchors: left text ends before the first year column and
        # the overruled column starts just after it.
        b1, b2, b3, b4 = bounds
        left, mid, y1, y2 = [], [], None, None
        for start, seg in segments(line):
            if YEAR.match(seg) and b2 - 4 <= start <= b2 + 10:
                y1 = int(seg)
            elif YEAR.match(seg) and start >= b4 - 6:
                y2 = int(seg)
            elif start < b2 + 4:
                left.append(seg)
            else:
                mid.append(seg)
        if y1 is not None:
            cur = {"year": y1, "left": [], "items": []}
            entries.append(cur)
        if cur is None:
            continue
        cur["left"] += left
        if y2 is not None or (mid and not cur["items"]):
            cur["items"].append({"year": y2, "text": []})
        if mid:
            cur["items"][-1]["text"] += mid
    rows = []
    for e in entries:
        left = " ".join(e["left"])
        for it in e["items"]:
            text = " ".join(it["text"])
            rows.append({
                "overruling_name": case_name(left),
                "overruling_year": e["year"],
                "overruling_cite": us_cite(left),
                "overruled_name": case_name(text),
                "overruled_year": it["year"] or "",
                "overruled_cite": us_cite(text),
                "partial": int("in part" in text.replace("\n", " ")),
            })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--table", type=Path, default=Path(__file__).parent / "data/raw/overruled_table.txt")
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "data/pairs_raw.csv")
    args = ap.parse_args()
    rows = parse(args.table.read_text(encoding="utf-8").splitlines())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} pairs -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
