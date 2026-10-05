#!/usr/bin/env python3
"""Score a TREC run on the SCOTUS-Overruled supersession-retrieval testbed.

    python score.py run.trec                       # metrics of one run
    python score.py run.trec --gate indicator      # apply the gold validity gate first
    python score.py run.trec --baseline base.trec  # paired deltas, cluster bootstrap

Run format: one line per retrieved document, `qid Q0 doc_id rank score tag`
(standard TREC). Documents that a system was not allowed to retrieve, i.e.
decided on or after the query date or equal to the query's source opinion
(`exclude_doc`), are dropped before scoring and counted in a warning.

Query sets (field `set` in queries.jsonl)
  post_full  cites the overruling case B after a full overruling; gold = B, stale = A
  post_part  as above, for partial overrulings
  pre        cites A before its first full overruling; gold = A
  control    cites a case that is not in the overruled table; gold = that case

Metrics: nDCG@10 (x100), Recall@10, MRR, stale@10 (share of queries whose top 10
contains the overruled case A) and stale-any@10 (share of top-10 documents
already fully overruled at the query date, from closures.tsv).
Only the Python standard library is used.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
SETS = ("post_full", "post_part", "pre", "control")


def load():
    queries = {}
    for line in open(DATA / "queries.jsonl", encoding="utf-8"):
        q = json.loads(line)
        queries[q["qid"]] = q
    gold = {int(r[0]): int(r[2]) for r in csv.reader(open(DATA / "qrels.tsv"), delimiter="\t")}
    stale = {int(r[0]): int(r[1]) for r in csv.reader(open(DATA / "stale.tsv"), delimiter="\t")}
    dates = {}
    with open(DATA / "corpus_ids.tsv", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            dates[int(r["doc_id"])] = r["decision_date"]
    full, part = {}, {}
    with open(DATA / "closures.tsv", encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["full_closure_date"]:
                full[int(r["doc_id"])] = r["full_closure_date"]
            if r["partial_closure_date"]:
                part[int(r["doc_id"])] = r["partial_closure_date"]
    return queries, gold, stale, dates, full, part


def read_run(path):
    run = defaultdict(list)
    for line in open(path, encoding="utf-8"):
        p = line.split()
        if len(p) >= 5:
            run[int(p[0])].append((int(p[2]), float(p[4])))
    for qid in run:
        run[qid].sort(key=lambda x: -x[1])
    return run


def admissible(run, queries, dates):
    """Drop documents decided on/after t_q, the source opinion, and unknown ids."""
    dropped = 0
    out = {}
    for qid, docs in run.items():
        q = queries.get(qid)
        if q is None:
            continue
        keep = [(d, s) for d, s in docs if d in dates and dates[d] < q["t_q"] and d != q["exclude_doc"]]
        dropped += len(docs) - len(keep)
        out[qid] = keep
    return out, dropped


def gate(docs, t_q, full, part, w=None):
    """Remove documents fully overruled by t_q; optionally scale partially overruled ones by w."""
    kept = [(d, s) for d, s in docs if not (d in full and full[d] <= t_q)]
    if w is None:
        return kept
    lo = min((s for _, s in kept), default=0.0)
    shift = (1e-9 - lo) if lo <= 0 else 0.0
    res = [(d, (s + shift) * (w if d in part and part[d] <= t_q else 1.0)) for d, s in kept]
    return sorted(res, key=lambda x: -x[1])


def metrics(ranked, gold, stale, t_q, full):
    ids = [d for d, _ in ranked]
    top = ids[:10]
    rank = ids.index(gold) + 1 if gold in ids else None
    m = {
        "ndcg@10": 100 / math.log2(rank + 1) if rank and rank <= 10 else 0.0,
        "recall@10": float(bool(rank and rank <= 10)),
        "mrr": 1 / rank if rank else 0.0,
        "stale_any@10": sum(1 for d in top if d in full and full[d] <= t_q) / max(1, len(top)),
    }
    if stale is not None:
        m["stale@10"] = float(stale in top)
    return m


def per_query(run, queries, gold, stale, full, part, args):
    out = {}
    for qid, q in queries.items():
        if args.exclude_gold_closed and q["gold_closed_at_tq"]:
            continue
        docs = run.get(qid, [])
        if args.gate == "indicator":
            docs = gate(docs, q["t_q"], full, part)
        elif args.gate == "weighted":
            docs = gate(docs, q["t_q"], full, part, args.w)
        out[qid] = metrics(docs, gold[qid], stale.get(qid), q["t_q"], full)
    return out


def summarize(pq, queries):
    res = {}
    for s in SETS:
        ids = [i for i in pq if queries[i]["set"] == s]
        if not ids:
            continue
        keys = pq[ids[0]].keys()
        res[s] = {"n": len(ids)} | {k: sum(pq[i][k] for i in ids) / len(ids) for k in keys}
    return res


def cluster_bootstrap(vals, n=10000, seed=13):
    """vals: list of (cluster, value). Returns mean and 95% CI over resampled clusters."""
    groups = defaultdict(list)
    for c, v in vals:
        groups[c].append(v)
    keys = list(groups)
    rng = random.Random(seed)
    stats = []
    for _ in range(n):
        tot = cnt = 0
        for _ in keys:
            g = groups[keys[rng.randrange(len(keys))]]
            tot += sum(g)
            cnt += len(g)
        stats.append(tot / cnt)
    stats.sort()
    mean = sum(v for _, v in vals) / len(vals)
    return mean, stats[int(0.025 * n)], stats[min(n - 1, int(0.975 * n))]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run")
    ap.add_argument("--gate", choices=["none", "indicator", "weighted"], default="none")
    ap.add_argument("--w", type=float, default=0.5, help="weight for partially overruled documents (--gate weighted)")
    ap.add_argument("--baseline", help="second TREC run (scored ungated) for paired deltas")
    ap.add_argument("--exclude-gold-closed", action="store_true",
                    help="drop the 4 queries whose gold case was itself overruled before t_q")
    ap.add_argument("--n-boot", type=int, default=10000)
    args = ap.parse_args()

    queries, gold, stale, dates, full, part = load()
    run, dropped = admissible(read_run(args.run), queries, dates)
    if dropped:
        print(f"warning: dropped {dropped} inadmissible documents (dated on/after t_q, source opinion, or unknown id)",
              file=sys.stderr)
    pq = per_query(run, queries, gold, stale, full, part, args)
    print(json.dumps({"run": args.run, "gate": args.gate, "sets": summarize(pq, queries)}, indent=1))

    if args.baseline:
        base, _ = admissible(read_run(args.baseline), queries, dates)
        args_b = argparse.Namespace(**{**vars(args), "gate": "none"})
        pb = per_query(base, queries, gold, stale, full, part, args_b)
        deltas = {}
        for s in SETS:
            for k in ("ndcg@10", "stale@10"):
                vals = [((f"q{i}" if s == "control" else f"p{queries[i]['pair']}"), pq[i][k] - pb[i][k])
                        for i in pq if queries[i]["set"] == s and k in pq[i] and i in pb]
                if vals:
                    m, lo, hi = cluster_bootstrap(vals, args.n_boot)
                    deltas[f"{s}|{k}"] = {"delta": m, "ci95": [lo, hi], "n": len(vals)}
        print(json.dumps({"paired_deltas_vs_baseline": deltas}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
