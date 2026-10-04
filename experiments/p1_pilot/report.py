#!/usr/bin/env python3
"""Render results.json into RESULTS.md (tables + acceptance verdict)."""

from __future__ import annotations

import json
import subprocess
import sys

from p1lib import HERE

DESIGN_COMMIT = "08aea76f2e923a1cc2d4828b39628d0e75d85407"


def fp(p):
    return "<0.0001" if p == 0 else f"{p:.4f}"


def f(x, nd=1):
    return "—" if x is None else f"{x:.{nd}f}"


def main() -> int:
    R = json.loads((HERE / "results.json").read_text())
    nq = R["n_queries"]
    L = ["# P1 pilot results", "",
         f"Design frozen at commit `{DESIGN_COMMIT}` (experiments/p1_pilot/DESIGN.md). "
         "Gold-treatment variant only (no ALERT extractor available; see Deviations).", "",
         f"Queries: post (full) {nq.get('post_full', 0)} in {R['n_clusters']['post_full']} pair clusters, "
         f"post (partial) {nq.get('post_part', 0)}, pre {nq.get('pre', 0)}, control {nq.get('control', 0)}. "
         f"Sanity check (gate never removes the gold case on pre-closure queries): "
         f"**{R['sanity_violations']} violations**.", ""]

    L += ["## Q1: how often do hosts retrieve already-overruled precedent?", "",
          "Share of post-closure queries (full overrulings) whose *ungated* ranking contains the overruled case A.", "",
          "| Host | A in top-10 | A in top-100 |", "|---|---|---|"]
    for h, H in R["hosts"].items():
        L.append(f"| {h} | {100 * H['prevalence_top10']:.1f}% | {100 * H['prevalence_top100']:.1f}% |")

    L += ["", "## Q2: effect of the gate (post-closure queries, full overrulings)", "",
          "nDCG@10 in points (×100); stale@10 = share of queries with A in the top 10.", "",
          "| Host | Condition | nDCG@10 | R@10 | MRR | stale@10 (A) | stale share@10 (any closed) |",
          "|---|---|---|---|---|---|---|"]
    for h, H in R["hosts"].items():
        for c in ("ungated", "indicator"):
            m = H["conditions"][c]["post_full"]
            L.append(f"| {h} | {c} | {f(m['ndcg'], 2)} | {f(100 * m['r10'])}% | {f(m['mrr'], 3)} | "
                     f"{f(100 * m['stale_a'])}% | {f(100 * m['stale_any'])}% |")

    L += ["", "### Paired deltas (indicator − ungated), cluster bootstrap by pair, Holm across hosts", "",
          "| Host | ΔnDCG@10 [95% CI] | p (Holm) | Δstale@10 [95% CI] | p (Holm) | ΔnDCG per-query CI |",
          "|---|---|---|---|---|---|"]
    verdict_hosts = []
    for h, H in R["hosts"].items():
        dn = H["deltas"]["indicator|post_full|ndcg"]
        ds = H["deltas"]["indicator|post_full|stale_a"]
        dc = H["deltas"]["indicator|control|ndcg"]
        L.append(f"| {h} | {dn['mean']:+.2f} [{dn['ci'][0]:+.2f}, {dn['ci'][1]:+.2f}] | {fp(dn.get('p_holm', dn['p']))} | "
                 f"{100 * ds['mean']:+.1f} [{100 * ds['ci'][0]:+.1f}, {100 * ds['ci'][1]:+.1f}] pts | {fp(ds.get('p_holm', ds['p']))} | "
                 f"[{dn['ci_perquery'][0]:+.2f}, {dn['ci_perquery'][1]:+.2f}] |")
        ok = (dn["mean"] > 0 and dn.get("p_holm", 1) < 0.05 and ds["mean"] < 0 and ds.get("p_holm", 1) < 0.05
              and dc["ci"][0] > -0.5)
        verdict_hosts.append((h, ok, dc))

    L += ["", "## Non-inferiority on no-stale control queries (margin −0.5 nDCG points)", "",
          "| Host | ΔnDCG@10 (indicator − ungated) [95% CI] | NI holds |", "|---|---|---|"]
    for h, ok, dc in verdict_hosts:
        L.append(f"| {h} | {dc['mean']:+.3f} [{dc['ci'][0]:+.3f}, {dc['ci'][1]:+.3f}] | {'yes' if dc['ci'][0] > -0.5 else 'no'} |")

    L += ["", "## Pre-closure queries (gate should be inert for the gold case)", "",
          "| Host | ΔnDCG@10 [95% CI] |", "|---|---|"]
    for h, H in R["hosts"].items():
        d = H["deltas"]["indicator|pre|ndcg"]
        L.append(f"| {h} | {d['mean']:+.3f} [{d['ci'][0]:+.3f}, {d['ci'][1]:+.3f}] |")

    L += ["", "## Partial overrulings: treatment-weight sweep (post-closure queries)", "",
          "ALERT's `w(·)` is not specified in the paper or released code, so a sweep is reported.", "",
          "| Host | w | nDCG@10 | ΔnDCG@10 vs ungated [95% CI] |", "|---|---|---|---|"]
    for h, H in R["hosts"].items():
        base = H["conditions"]["ungated"].get("post_part")
        if not base:
            continue
        L.append(f"| {h} | ungated | {f(base['ndcg'], 2)} | — |")
        for w in ("0.25", "0.5", "0.75"):
            c = f"ind+w={w}"
            d = H["deltas"].get(f"{c}|post_part|ndcg")
            m = H["conditions"][c]["post_part"]
            L.append(f"| {h} | {w} | {f(m['ndcg'], 2)} | {d['mean']:+.2f} [{d['ci'][0]:+.2f}, {d['ci'][1]:+.2f}] |")

    n_ok = sum(ok for _, ok, _ in verdict_hosts)
    L += ["", "## Verdict against the pre-fixed acceptance criterion (DESIGN.md §7)", "",
          f"Hosts meeting all conditions (ΔnDCG > 0 and Δstale < 0, both Holm p < 0.05, NI on controls): "
          f"**{n_ok} of {len(verdict_hosts)}** "
          f"({', '.join(h for h, ok, _ in verdict_hosts if ok) or 'none'}).",
          f"Pilot **{'supports' if n_ok >= 2 else 'does not support'}** transfer under the gold-treatment variant."]
    (HERE / "RESULTS_TABLES.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
