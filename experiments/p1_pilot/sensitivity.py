#!/usr/bin/env python3
"""POST-HOC sensitivity analysis (not part of the frozen design).

Written after the primary results were seen. A few post-closure queries have a
gold case B that was itself fully overruled before the query date (overruling
chains), so the indicator gate removes the gold. DESIGN.md §5 treats an
authority closed before t_q as non-relevant, so these gold labels contradict
the design's own judgment rule. This script re-runs the primary endpoints with
those queries excluded. The verdict in RESULTS.md stays the pre-specified one.
"""

from __future__ import annotations

import json
import sys

from evaluate import HOSTS, RUNS, bootstrap, closures, cluster_key, gate, holm, per_query
from p1lib import HERE, WORK


def main() -> int:
    queries = {q["qid"]: q for q in (json.loads(l) for l in open(WORK / "queries.jsonl", encoding="utf-8"))}
    full, part = closures()
    post = [q for q in queries.values() if q["role"] == "post" and not q["partial"]]
    bad = [q["qid"] for q in post if q["gold_id"] in full and full[q["gold_id"]] <= q["t_q"]]
    out = {"excluded_qids": bad, "hosts": {}}
    for host in HOSTS:
        path = RUNS / f"{host}.jsonl"
        if not path.exists():
            continue
        runs = {r["qid"]: r["docs"] for r in (json.loads(l) for l in open(path))}
        H = {}
        for metric in ("ndcg", "stale_a"):
            d = {}
            for q in post:
                if q["qid"] in bad or q["qid"] not in runs:
                    continue
                docs = runs[q["qid"]]
                u = per_query(q, [x for x, _ in docs], full)[metric]
                g = per_query(q, gate(docs, q["t_q"], full, part), full)[metric]
                d[q["qid"]] = (cluster_key(q), g - u)
            m, lo, hi, p = bootstrap(d, True)
            H[metric] = {"mean": m, "ci": [lo, hi], "p": p, "n": len(d)}
        out["hosts"][host] = H
    for metric in ("ndcg", "stale_a"):
        for h, p in holm({h: out["hosts"][h][metric]["p"] for h in out["hosts"]}).items():
            out["hosts"][h][metric]["p_holm"] = p
    (HERE / "sensitivity.json").write_text(json.dumps(out, indent=1))
    print(f"excluded {len(bad)} queries: {bad}")
    for h, H in out["hosts"].items():
        n, s = H["ndcg"], H["stale_a"]
        print(f"{h}: dnDCG {n['mean']:+.3f} [{n['ci'][0]:+.3f}, {n['ci'][1]:+.3f}] p_holm {n['p_holm']:.4f}; "
              f"dstale {100*s['mean']:+.1f} [{100*s['ci'][0]:+.1f}, {100*s['ci'][1]:+.1f}] p_holm {s['p_holm']:.4f} (n={n['n']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
