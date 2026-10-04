#!/usr/bin/env python3
"""Apply the validity gate to host runs and evaluate (DESIGN.md §5–§7).

Conditions per host
  ungated        host ranking
  indicator      drop documents whose interval closed by t_q (full overrulings)
  ind+w=<w>      indicator, plus partially overruled documents (closed by t_q)
                 get their min-shifted score multiplied by w
Gold closures: CONAN table entries matched to CAP (pairs.csv and matched rows of
pairs_excluded.csv); a document's interval end is its earliest *full*
overruling date, and its partial-closure date its earliest partial one.

Query sets
  post_full   post-closure queries of fully overruled pairs (primary)
  post_part   post-closure queries of partially overruled pairs
  pre         pre-closure queries (sanity: the gate must never remove A)
  control     no-stale control queries (non-inferiority)
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import defaultdict

from p1lib import HERE, WORK, mrr, ndcg_at, recall_at

RUNS = HERE / "runs"
HOSTS = ["bm25", "bge", "legalbert"]
WEIGHTS = [0.25, 0.5, 0.75]
N_BOOT = 10000
SEED = 13
NI_MARGIN = 0.5  # nDCG points


def closures():
    full, part = {}, {}
    for fname in ("pairs.csv", "pairs_excluded.csv"):
        for r in csv.DictReader(open(HERE / "data" / fname, encoding="utf-8")):
            if not r.get("a_id") or not r.get("b_date"):
                continue
            a, d = int(r["a_id"]), r["b_date"]
            tgt = part if r["partial"] == "1" else full
            if a not in tgt or d < tgt[a]:
                tgt[a] = d
    return full, part


def gate(docs, t_q, full, part, w=None):
    """docs: [[id, score], ...] sorted desc. Returns gated ranked id list."""
    kept = [(d, s) for d, s in docs if not (d in full and full[d] <= t_q)]
    if w is None or not kept:
        return [d for d, _ in kept]
    # Multiply the host score by w (P1's form). Only if some scores are
    # non-positive, shift them to be positive first so that w < 1 still demotes.
    lo = min(s for _, s in kept)
    shift = (1e-9 - lo) if lo <= 0 else 0.0
    rescored = []
    for d, s in kept:
        s2 = s + shift
        if d in part and part[d] <= t_q:
            s2 *= w
        rescored.append((d, s2))
    rescored.sort(key=lambda x: -x[1])
    return [d for d, _ in rescored]


def per_query(q, ranked, full):
    gold = q["gold_id"]
    m = {"ndcg": 100 * ndcg_at(ranked, gold), "r10": recall_at(ranked, gold), "mrr": mrr(ranked, gold)}
    stale = q["stale_id"]
    m["stale_a"] = float(stale != "" and int(stale) in ranked[:10]) if stale != "" else None
    top = ranked[:10]
    m["stale_any"] = sum(1 for d in top if d in full and full[d] <= q["t_q"]) / max(1, len(top))
    return m


def cluster_key(q):
    return f"q{q['qid']}" if q["role"] == "control" else f"p{q['pair']}"


def bootstrap(deltas: dict, clustered=True, n=N_BOOT, seed=SEED):
    """deltas: {qid: (cluster, value)}. Returns mean, 95% CI, two-sided p."""
    rng = random.Random(seed)
    groups = defaultdict(list)
    for c, v in deltas.values():
        groups[c if clustered else id(v) if False else c].append(v)
    if not clustered:
        groups = {i: [v] for i, (_, v) in enumerate(deltas.values())}
    keys = list(groups)
    obs = sum(v for vs in groups.values() for v in vs) / sum(len(vs) for vs in groups.values())
    stats = []
    for _ in range(n):
        tot = cnt = 0
        for _ in keys:
            vs = groups[keys[rng.randrange(len(keys))]]
            tot += sum(vs); cnt += len(vs)
        stats.append(tot / cnt)
    stats.sort()
    lo, hi = stats[int(0.025 * n)], stats[min(n - 1, int(0.975 * n))]
    p = min(1.0, 2 * min(sum(1 for s in stats if s <= 0) / n, sum(1 for s in stats if s >= 0) / n))
    return obs, lo, hi, p


def holm(ps: dict) -> dict:
    items = sorted(ps.items(), key=lambda kv: kv[1])
    out, run = {}, 0.0
    for i, (k, p) in enumerate(items):
        run = max(run, min(1.0, (len(items) - i) * p))
        out[k] = run
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hosts", nargs="+", default=HOSTS)
    ap.add_argument("--n-boot", type=int, default=N_BOOT)
    args = ap.parse_args()
    queries = {q["qid"]: q for q in (json.loads(l) for l in open(WORK / "queries.jsonl", encoding="utf-8"))}
    full, part = closures()

    def qset(q):
        if q["role"] == "post":
            return "post_part" if q["partial"] else "post_full"
        return q["role"]

    results = {"hosts": {}, "n_queries": defaultdict(int), "n_clusters": {}}
    for q in queries.values():
        results["n_queries"][qset(q)] += 1
    results["n_clusters"]["post_full"] = len({cluster_key(q) for q in queries.values() if qset(q) == "post_full"})

    sanity_violations = 0
    for host in args.hosts:
        path = RUNS / f"{host}.jsonl"
        if not path.exists():
            print(f"skip {host}: no run file")
            continue
        runs = {r["qid"]: r["docs"] for r in (json.loads(l) for l in open(path))}
        conds = {"ungated": None, "indicator": "ind"} | {f"ind+w={w}": w for w in WEIGHTS}
        pq = {c: {} for c in conds}
        for qid, docs in runs.items():
            q = queries[qid]
            ranked_u = [d for d, _ in docs]
            pq["ungated"][qid] = per_query(q, ranked_u, full)
            r_ind = gate(docs, q["t_q"], full, part)
            pq["indicator"][qid] = per_query(q, r_ind, full)
            if q["role"] == "pre" and q["gold_id"] in ranked_u and q["gold_id"] not in r_ind:
                sanity_violations += 1
            for c, w in conds.items():
                if c.startswith("ind+w"):
                    pq[c][qid] = per_query(q, gate(docs, q["t_q"], full, part, w), full)

        H = {"conditions": {}, "deltas": {}}
        for c in conds:
            agg = {}
            for s in ("post_full", "post_part", "pre", "control"):
                ids = [i for i in pq[c] if qset(queries[i]) == s]
                if not ids:
                    continue
                m = {k: sum(pq[c][i][k] for i in ids) / len(ids) for k in ("ndcg", "r10", "mrr", "stale_any")}
                sa = [pq[c][i]["stale_a"] for i in ids if pq[c][i]["stale_a"] is not None]
                m["stale_a"] = sum(sa) / len(sa) if sa else None
                m["n"] = len(ids)
                agg[s] = m
            H["conditions"][c] = agg
        # prevalence (Q1): ungated top-10 / top-100 containing A, post_full
        ids = [i for i in runs if qset(queries[i]) == "post_full"]
        H["prevalence_top10"] = sum(int(queries[i]["stale_id"]) in [d for d, _ in runs[i]][:10] for i in ids) / len(ids)
        H["prevalence_top100"] = sum(int(queries[i]["stale_id"]) in [d for d, _ in runs[i]] for i in ids) / len(ids)
        # paired deltas with bootstrap
        for c in [k for k in conds if k != "ungated"]:
            for s, metric in (("post_full", "ndcg"), ("post_full", "stale_a"), ("post_full", "stale_any"),
                              ("post_part", "ndcg"), ("pre", "ndcg"), ("control", "ndcg")):
                d = {i: (cluster_key(queries[i]), pq[c][i][metric] - pq["ungated"][i][metric])
                     for i in pq[c] if qset(queries[i]) == s and pq[c][i][metric] is not None}
                if not d:
                    continue
                cl = bootstrap(d, True, args.n_boot)
                iq = bootstrap(d, False, args.n_boot)
                H["deltas"][f"{c}|{s}|{metric}"] = {"mean": cl[0], "ci": [cl[1], cl[2]], "p": cl[3],
                                                     "ci_perquery": [iq[1], iq[2]], "p_perquery": iq[3]}
        results["hosts"][host] = H
        print(f"{host}: done")

    # Holm across hosts (indicator condition, primary endpoints)
    for metric in ("ndcg", "stale_a"):
        ps = {h: results["hosts"][h]["deltas"][f"indicator|post_full|{metric}"]["p"] for h in results["hosts"]}
        for h, p in holm(ps).items():
            results["hosts"][h]["deltas"][f"indicator|post_full|{metric}"]["p_holm"] = p
    results["sanity_violations"] = sanity_violations
    out = HERE / "results.json"
    out.write_text(json.dumps(results, indent=1))
    print(f"sanity violations: {sanity_violations}; wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
