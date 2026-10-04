#!/usr/bin/env python3
"""Build the U.S. Supreme Court corpus from CAP volume zips (CC0).

Writes data/work/corpus.jsonl, one case per line:
  id, cite ("V U.S. P"), name, date (YYYY-MM-DD), opinions: [{type, text}],
  cites_to: [{cite, case_ids, opinion_index}]
Only opinion text is kept (no head matter, which carries reporter notes).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def official_cite(case: dict) -> str:
    for c in case.get("citations", []):
        if c.get("type") == "official":
            m = re.match(r"(\d+)\s+U\.\s?S\.\s+(\d+)", c["cite"])
            if m:
                return f"{m.group(1)} U.S. {m.group(2)}"
    return ""


def normalize_date(d: str) -> str:
    # CAP dates may be "YYYY", "YYYY-MM" or "YYYY-MM-DD".
    parts = (d or "").split("-")
    while len(parts) < 3:
        parts.append("01")
    return "-".join(parts[:3])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--zips", type=Path, default=HERE / "data/raw/cap_us")
    ap.add_argument("--out", type=Path, default=HERE / "data/work/corpus.jsonl")
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(args.out, "w", encoding="utf-8") as out:
        for zp in sorted(args.zips.glob("*.zip"), key=lambda p: int(p.stem)):
            with zipfile.ZipFile(zp) as z:
                for name in sorted(z.namelist()):
                    if not name.startswith("json/") or not name.endswith(".json"):
                        continue
                    case = json.loads(z.read(name))
                    ops = [{"type": o.get("type", ""), "text": o.get("text", "")}
                           for o in case.get("casebody", {}).get("opinions", [])]
                    rec = {
                        "id": case["id"],
                        "cite": official_cite(case),
                        "name": case.get("name_abbreviation", ""),
                        "date": normalize_date(case.get("decision_date", "")),
                        "opinions": ops,
                        "cites_to": [
                            {"cite": c.get("cite", ""), "case_ids": c.get("case_ids", []),
                             "opinion_index": c.get("opinion_index", 0)}
                            for c in case.get("cites_to", []) if c.get("case_ids")
                        ],
                    }
                    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    n += 1
    print(f"{n} cases -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
