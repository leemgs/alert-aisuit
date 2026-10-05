#!/usr/bin/env python3
"""Write the testbed corpus (data/docs.jsonl) from the CAP-derived corpus.

    python make_corpus.py ../../experiments/p1_pilot/data/work/corpus.jsonl

The input is produced by experiments/p1_pilot (download_cap.sh, then
build_corpus.py). Only the 29,030 opinions listed in data/corpus_ids.tsv are
kept. Each output line is {"doc_id", "decision_date", "cite", "name", "text"}.
The text is all opinions of the case, joined by newlines.
"""

import csv
import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"


def main() -> int:
    keep = {int(r["doc_id"]) for r in csv.DictReader(open(DATA / "corpus_ids.tsv", encoding="utf-8"), delimiter="\t")}
    n = 0
    with open(sys.argv[1], encoding="utf-8") as f, open(DATA / "docs.jsonl", "w", encoding="utf-8") as out:
        for line in f:
            r = json.loads(line)
            if r["id"] in keep:
                text = "\n".join(o["text"] for o in r["opinions"])
                out.write(json.dumps({"doc_id": r["id"], "decision_date": r["date"], "cite": r["cite"],
                                      "name": r["name"], "text": text}, ensure_ascii=False) + "\n")
                n += 1
    print(f"wrote {n} documents to {DATA / 'docs.jsonl'} (expected {len(keep)})")
    return 0 if n == len(keep) else 1


if __name__ == "__main__":
    sys.exit(main())
