#!/usr/bin/env python3
"""Match CONAN table entries to CAP case ids and apply the pre-fixed exclusions.

Output: data/pairs.csv (usable pairs) and data/pairs_excluded.csv (with reason).
Exclusions (fixed in DESIGN.md / RESULTS deviation log):
  * overruling decision on/after 2020-01-01;
  * overruling (B) or overruled (A) decision not found in the CAP corpus;
  * A or B opinion text shorter than MIN_CHARS.
When several CAP cases share a cite (orders on the same page), the candidate
whose year matches the table and whose name shares a party word wins; ties go
to the longest opinion.
"""

from __future__ import annotations

import csv
import re
import sys
from collections import defaultdict

from p1lib import HERE, MIN_CHARS, doc_text, iter_corpus


def words(name: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{4,}", name.lower())}


def pick(cands, year: str, name: str):
    if not cands:
        return None
    def key(c):
        _id, date, length, cname = c
        return (date[:4] == str(year), len(words(cname) & words(name)), length)
    return max(cands, key=key)


def main() -> int:
    by_cite = defaultdict(list)
    for r in iter_corpus():
        if r["cite"]:
            by_cite[r["cite"]].append((r["id"], r["date"], len(doc_text(r)), r["name"]))
    kept, dropped = [], []
    with open(HERE / "data/pairs_raw.csv", encoding="utf-8") as f:
        for p in csv.DictReader(f):
            reason = ""
            a = pick(by_cite.get(p["overruled_cite"], []), p["overruled_year"], p["overruled_name"])
            b = pick(by_cite.get(p["overruling_cite"], []), p["overruling_year"], p["overruling_name"]) if p["overruling_cite"] else None
            if int(p["overruling_year"]) >= 2020:
                reason = "overruled on/after 2020 (ALERT window)"
            elif b is None:
                reason = "overruling decision not in CAP corpus"
            elif a is None:
                reason = "overruled decision not in CAP corpus"
            elif a[2] < MIN_CHARS or b[2] < MIN_CHARS:
                reason = f"opinion text < {MIN_CHARS} chars"
            row = {**p,
                   "a_id": a[0] if a else "", "a_date": a[1] if a else "",
                   "b_id": b[0] if b else "", "b_date": b[1] if b else ""}
            (dropped if reason else kept).append({**row, "reason": reason} if reason else row)
    for name, rows in (("pairs.csv", kept), ("pairs_excluded.csv", dropped)):
        with open(HERE / "data" / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    reasons = defaultdict(int)
    for r in dropped:
        reasons[r["reason"]] += 1
    print(f"kept {len(kept)} pairs; excluded {len(dropped)}: {dict(reasons)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
