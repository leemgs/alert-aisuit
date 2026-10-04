# P1 pilot results

Design frozen at commit `08aea76f2e923a1cc2d4828b39628d0e75d85407` (experiments/p1_pilot/DESIGN.md). Gold-treatment variant only (no ALERT extractor available; see Deviations).

Queries: post (full) 984 in 208 pair clusters, post (partial) 149, pre 1061, control 1133. Sanity check (gate never removes the gold case on pre-closure queries): **0 violations**.

## Q1: how often do hosts retrieve already-overruled precedent?

Share of post-closure queries (full overrulings) whose *ungated* ranking contains the overruled case A.

| Host | A in top-10 | A in top-100 |
|---|---|---|
| bm25 | 8.3% | 26.8% |

## Q2: effect of the gate (post-closure queries, full overrulings)

nDCG@10 in points (×100); stale@10 = share of queries with A in the top 10.

| Host | Condition | nDCG@10 | R@10 | MRR | stale@10 (A) | stale share@10 (any closed) |
|---|---|---|---|---|---|---|
| bm25 | ungated | 28.88 | 42.0% | 0.258 | 8.3% | 3.4% |
| bm25 | indicator | 28.97 | 42.0% | 0.259 | 0.0% | 0.0% |

### Paired deltas (indicator − ungated), cluster bootstrap by pair, Holm across hosts

| Host | ΔnDCG@10 [95% CI] | p (Holm) | Δstale@10 [95% CI] | p (Holm) | ΔnDCG per-query CI |
|---|---|---|---|---|---|
| bm25 | +0.09 [-0.58, +0.52] | 0.6570 | -8.3 [-10.7, -6.2] pts | 0.0000 | [-0.30, +0.42] |

## Non-inferiority on no-stale control queries (margin −0.5 nDCG points)

| Host | ΔnDCG@10 (indicator − ungated) [95% CI] | NI holds |
|---|---|---|
| bm25 | +0.089 [+0.035, +0.162] | yes |

## Pre-closure queries (gate should be inert for the gold case)

| Host | ΔnDCG@10 [95% CI] |
|---|---|
| bm25 | +0.177 [+0.075, +0.305] |

## Partial overrulings: treatment-weight sweep (post-closure queries)

ALERT's `w(·)` is not specified in the paper or released code, so a sweep is reported.

| Host | w | nDCG@10 | ΔnDCG@10 vs ungated [95% CI] |
|---|---|---|---|
| bm25 | ungated | 39.66 | — |
| bm25 | 0.25 | 39.95 | +0.29 [+0.04, +0.65] |
| bm25 | 0.5 | 39.95 | +0.29 [+0.04, +0.65] |
| bm25 | 0.75 | 39.95 | +0.29 [+0.04, +0.65] |

## Verdict against the pre-fixed acceptance criterion (DESIGN.md §7)

Hosts meeting all conditions (ΔnDCG > 0 and Δstale < 0, both Holm p < 0.05, NI on controls): **0 of 1** (none).
Pilot **does not support** transfer under the gold-treatment variant.
