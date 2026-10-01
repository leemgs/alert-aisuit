#!/usr/bin/env python3
"""Compute the statistics ACL reviewers asked for, from exported experiment outputs.

Every input is a small CSV (formats in README.md and templates/). Any input may be
omitted; the matching statistics are then skipped. Outputs:

  review_stats.md   human-readable report
  review_stats.tex  \\newcommand macros to paste into the paper

Covered review items:
  W-A / W1  PLRE pair counts, positive rate, distractor share, test size;
            bootstrap CIs for the temporal ablation and PLRE comparison tables
  W2        PLRE F1 without stale-authority distractors
  W-A / W3  number of human-adjudicated RQ1 test cases; split overlap check
  W-B       LLM calls and tokens per case for each system
  W-C       component ablation on the human-adjudicated subset
  W-E       Fleiss' kappa / Krippendorff's alpha for >2 annotators
  W-F       per-archetype PLRE F1
  W4        calibration-set size
  W5        RQ2 inter-rater agreement and Holm-corrected Wilcoxon tests

Only the Python standard library is required. If SciPy is installed, exact
Wilcoxon p-values are used; otherwise a normal approximation, which can differ
from the exact value by up to about 0.03 at n = 15. Install SciPy for the paper.
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import statistics
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


def read_csv(path: Path | None, required: list[str]) -> list[dict] | None:
    if path is None:
        return None
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if rows:
        missing = [c for c in required if c not in rows[0]]
        if missing:
            sys.exit(f"{path}: missing columns {missing}")
    return rows


def fmt(x: float | None, nd: int = 2) -> str:
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{nd}f}"


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def binary_prf(gold: list[int], pred: list[int]) -> tuple[float, float, float]:
    tp = sum(1 for g, p in zip(gold, pred) if g == 1 and p == 1)
    fp = sum(1 for g, p in zip(gold, pred) if g == 0 and p == 1)
    fn = sum(1 for g, p in zip(gold, pred) if g == 1 and p == 0)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return prec, rec, f1


def macro_prf(gold: list[str], pred: list[str]) -> tuple[float, float, float]:
    labels = sorted(set(gold) | set(pred))
    ps, rs, fs = [], [], []
    for lab in labels:
        g = [1 if x == lab else 0 for x in gold]
        p = [1 if x == lab else 0 for x in pred]
        pr, rc, f = binary_prf(g, p)
        ps.append(pr), rs.append(rc), fs.append(f)
    return statistics.mean(ps), statistics.mean(rs), statistics.mean(fs)


def bootstrap_ci(items: list, metric, n_boot: int, seed: int, alpha: float = 0.05):
    """Percentile CI of metric(items_resampled)."""
    rng = random.Random(seed)
    n = len(items)
    vals = []
    for _ in range(n_boot):
        sample = [items[rng.randrange(n)] for _ in range(n)]
        vals.append(metric(sample))
    vals.sort()
    lo = vals[int((alpha / 2) * n_boot)]
    hi = vals[min(n_boot - 1, int((1 - alpha / 2) * n_boot))]
    return lo, hi


def paired_bootstrap(items: list, metric_a, metric_b, n_boot: int, seed: int):
    """Two-sided paired bootstrap test of metric_a - metric_b on shared items.

    Returns (observed difference, 95% CI of the difference, two-sided p-value).
    """
    rng = random.Random(seed)
    n = len(items)
    obs = metric_a(items) - metric_b(items)
    diffs = []
    for _ in range(n_boot):
        sample = [items[rng.randrange(n)] for _ in range(n)]
        diffs.append(metric_a(sample) - metric_b(sample))
    diffs.sort()
    lo, hi = diffs[int(0.025 * n_boot)], diffs[min(n_boot - 1, int(0.975 * n_boot))]
    le0 = sum(1 for d in diffs if d <= 0) / n_boot
    ge0 = sum(1 for d in diffs if d >= 0) / n_boot
    p = min(1.0, 2 * min(le0, ge0))
    return obs, (lo, hi), p


def cohen_kappa(a: list[str], b: list[str]) -> float:
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def fleiss_kappa(table: list[list[str]]) -> float:
    """table: one list of labels per item, all items with the same number of raters."""
    cats = sorted({x for row in table for x in row})
    n_items, n_raters = len(table), len(table[0])
    p_j = defaultdict(float)
    p_i = []
    for row in table:
        c = Counter(row)
        for k in cats:
            p_j[k] += c[k]
        p_i.append((sum(v * v for v in c.values()) - n_raters) / (n_raters * (n_raters - 1)))
    total = n_items * n_raters
    pe = sum((p_j[k] / total) ** 2 for k in cats)
    pbar = statistics.mean(p_i)
    return (pbar - pe) / (1 - pe) if pe < 1 else 1.0


def krippendorff_alpha(units: dict[str, list], level: str = "nominal") -> float:
    """units: item -> list of ratings (missing ratings simply omitted)."""
    pairable = {u: v for u, v in units.items() if len(v) >= 2}
    values = [x for v in pairable.values() for x in v]
    n = len(values)
    if n < 2:
        return float("nan")

    if level == "interval":
        def delta(a, b):
            return (float(a) - float(b)) ** 2
    else:
        def delta(a, b):
            return 0.0 if a == b else 1.0

    d_o = 0.0
    for v in pairable.values():
        m = len(v)
        d_o += sum(delta(a, b) for i, a in enumerate(v) for j, b in enumerate(v) if i != j) / (m - 1)
    d_o /= n
    d_e = sum(delta(a, b) for i, a in enumerate(values) for j, b in enumerate(values) if i != j)
    d_e /= n * (n - 1)
    return 1.0 - d_o / d_e if d_e > 0 else 1.0


def wilcoxon_signed_rank(x: list[float], y: list[float]) -> float:
    """Two-sided Wilcoxon signed-rank p-value (zero differences dropped)."""
    try:
        from scipy.stats import wilcoxon  # type: ignore

        diffs = [a - b for a, b in zip(x, y)]
        if all(d == 0 for d in diffs):
            return 1.0
        return float(wilcoxon(x, y, zero_method="wilcox").pvalue)
    except ImportError:
        pass
    d = [a - b for a, b in zip(x, y) if a != b]
    n = len(d)
    if n == 0:
        return 1.0
    ranked = sorted(range(n), key=lambda i: abs(d[i]))
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs(d[ranked[j + 1]]) == abs(d[ranked[i]]):
            j += 1
        for k in range(i, j + 1):
            ranks[ranked[k]] = (i + j) / 2 + 1
        i = j + 1
    w_plus = sum(r for r, di in zip(ranks, d) if di > 0)
    mu = n * (n + 1) / 4
    sigma = math.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    z = (w_plus - mu) / sigma if sigma else 0.0
    return math.erfc(abs(z) / math.sqrt(2))


def fmt_p(p: float, n_boot: int) -> str:
    """A bootstrap p-value of 0 only means p < 1/n_boot."""
    return f"<{1 / n_boot:.4f}" if p == 0 else f"{p:.4f}"


def holm(pvals: dict) -> dict:
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    adj, running = {}, 0.0
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        adj[k] = running
    return adj


# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------


class Report:
    def __init__(self) -> None:
        self.md: list[str] = []
        self.tex: dict[str, str] = {}

    def h(self, text: str) -> None:
        self.md.append(f"\n## {text}\n")

    def line(self, text: str = "") -> None:
        self.md.append(text)

    def macro(self, name: str, value: str) -> None:
        # LaTeX macro names may contain letters only.
        words = "Zero One Two Three Four Five Six Seven Eight Nine".split()
        clean = "".join(words[int(ch)] if ch.isdigit() else ch for ch in name if ch.isalnum())
        self.tex[clean] = value


def section_rq1(rows, rep: Report, args) -> None:
    rep.h("RQ1: severity labels (W-A, W3, W-C)")
    by_sys = defaultdict(dict)
    meta = {}
    for r in rows:
        by_sys[r["system"]][r["case_id"]] = r["pred"]
        meta[r["case_id"]] = (r["split"], r["label_source"], r["gold"])

    test_cases = [c for c, (sp, _, _) in meta.items() if sp == "test"]
    src = Counter(meta[c][1] for c in test_cases)
    rep.line(f"- Test cases: {len(test_cases)} (human: {src.get('human', 0)}, retained: {src.get('retained', 0)})")
    rep.macro("rqOneTestN", str(len(test_cases)))
    rep.macro("rqOneHumanTestN", str(src.get("human", 0)))

    human_all = [c for c, (_, s, _) in meta.items() if s == "human"]
    split_of_human = Counter(meta[c][0] for c in human_all)
    rep.line(f"- Human-adjudicated cases by split: {dict(split_of_human)}")
    if split_of_human.get("train", 0) or split_of_human.get("validation", 0):
        rep.line("  - NOTE: some human-adjudicated cases are in train/validation. If Table 3 "
                 "uses all human cases, those used for few-shot examples or threshold tuning "
                 "overlap the evaluation (possible leakage).")

    for subset_name, subset in (("human-adjudicated test", [c for c in test_cases if meta[c][1] == "human"]),
                                ("full test", test_cases)):
        if not subset:
            continue
        rep.line(f"\n**{subset_name} (n={len(subset)})**\n")
        rep.line("| System | F1 | 95% CI | P | R | Δ vs ALERT | p (paired bootstrap) |")
        rep.line("|---|---|---|---|---|---|---|")
        ref = args.reference_system
        for system in sorted(by_sys):
            cases = [c for c in subset if c in by_sys[system]]
            if not cases:
                continue

            def f1_of(sample, s=system):
                return macro_prf([meta[c][2] for c in sample], [by_sys[s][c] for c in sample])[2]

            p, r, f = macro_prf([meta[c][2] for c in cases], [by_sys[system][c] for c in cases])
            lo, hi = bootstrap_ci(cases, f1_of, args.n_boot, args.seed)
            diff_s = p_s = "—"
            if system != ref and ref in by_sys:
                shared = [c for c in cases if c in by_sys[ref]]

                def f1_ref(sample):
                    return macro_prf([meta[c][2] for c in sample], [by_sys[ref][c] for c in sample])[2]

                d, _, pv = paired_bootstrap(shared, f1_ref, f1_of, args.n_boot, args.seed)
                diff_s, p_s = f"{d:+.3f}", fmt_p(pv, args.n_boot)
            rep.line(f"| {system} | {f:.3f} | [{lo:.3f}, {hi:.3f}] | {p:.3f} | {r:.3f} | {diff_s} | {p_s} |")


def section_plre(rows, rep: Report, args) -> None:
    rep.h("PLRE (W-A/W1, W2, W-F)")
    test = [r for r in rows if r.get("split", "test") == "test"]
    pairs = {r["pair_id"]: r for r in test}
    n_pairs = len(pairs)
    pos = sum(1 for r in pairs.values() if r["gold"] == "1")
    distr = sum(1 for r in pairs.values() if r["is_distractor"] == "1")
    arche = Counter(r["archetype"] for r in pairs.values())
    all_pairs = {r["pair_id"] for r in rows}
    rep.line(f"- Pairs (all splits): {len(all_pairs)}; test pairs: {n_pairs}")
    rep.line(f"- Test positive rate: {pos / n_pairs:.3f} ({pos}/{n_pairs})")
    rep.line(f"- Test stale-authority distractor share: {distr / n_pairs:.3f} ({distr}/{n_pairs})")
    rep.line(f"- Test pairs per archetype: {dict(arche)}")
    rep.macro("plreNPairs", f"{len(all_pairs):,}".replace(",", "{,}"))
    rep.macro("plreTestPairs", str(n_pairs))
    rep.macro("plrePosRate", f"{100 * pos / n_pairs:.1f}")
    rep.macro("plreDistractorShare", f"{100 * distr / n_pairs:.1f}")

    by_sys = defaultdict(dict)
    stale = defaultdict(dict)
    for r in test:
        by_sys[r["system"]][r["pair_id"]] = int(r["pred"])
        if r.get("stale_cite", "") != "":
            stale[r["system"]][r["pair_id"]] = int(r["stale_cite"])
    gold = {pid: int(r["gold"]) for pid, r in pairs.items()}

    def f1_on(system, ids):
        return binary_prf([gold[i] for i in ids], [by_sys[system][i] for i in ids])[2]

    ref, flat = args.reference_system, args.flat_system
    for title, ids_filter in (("all test pairs", lambda r: True),
                              ("without stale-authority distractors (W2)", lambda r: r["is_distractor"] != "1")):
        ids = [pid for pid, r in pairs.items() if ids_filter(r)]
        rep.line(f"\n**{title} (n={len(ids)})**\n")
        rep.line("| System | F1 | 95% CI | P | R | Stale-cite % | Δ vs ALERT | p |")
        rep.line("|---|---|---|---|---|---|---|---|")
        for system in sorted(by_sys):
            sids = [i for i in ids if i in by_sys[system]]
            if not sids:
                continue
            p, r_, f = binary_prf([gold[i] for i in sids], [by_sys[system][i] for i in sids])
            lo, hi = bootstrap_ci(sids, lambda s, sy=system: f1_on(sy, s), args.n_boot, args.seed)
            st = (f"{100 * statistics.mean(stale[system][i] for i in sids if i in stale[system]):.1f}"
                  if stale.get(system) else "—")
            d_s = p_s = "—"
            if system != ref and ref in by_sys:
                shared = [i for i in sids if i in by_sys[ref]]
                d, _, pv = paired_bootstrap(shared, lambda s: f1_on(ref, s),
                                            lambda s, sy=system: f1_on(sy, s), args.n_boot, args.seed)
                d_s, p_s = f"{d:+.3f}", fmt_p(pv, args.n_boot)
            rep.line(f"| {system} | {f:.3f} | [{lo:.3f}, {hi:.3f}] | {p:.3f} | {r_:.3f} | {st} | {d_s} | {p_s} |")
            key = "All" if title.startswith("all") else "NoDistr"
            if system == ref:
                rep.macro(f"plreF{key}Full", f"{f:.2f}")
                rep.macro(f"plreCI{key}Full", f"[{lo:.2f}, {hi:.2f}]")
            if system == flat:
                rep.macro(f"plreF{key}Flat", f"{f:.2f}")
                rep.macro(f"plreCI{key}Flat", f"[{lo:.2f}, {hi:.2f}]")

    if ref in by_sys:
        rep.line("\n**Per-archetype F1 (W-F)**\n")
        systems = [s for s in (ref, flat) if s in by_sys]
        rep.line("| Archetype | n | " + " | ".join(systems) + " |")
        rep.line("|---|---|" + "---|" * len(systems))
        for a in sorted(arche):
            ids = [pid for pid, r in pairs.items() if r["archetype"] == a]
            cells = [f"{f1_on(s, [i for i in ids if i in by_sys[s]]):.3f}" for s in systems]
            rep.line(f"| {a} | {len(ids)} | " + " | ".join(cells) + " |")


def section_agreement(rows, rep: Report, title: str, prefix: str) -> None:
    rep.h(title)
    items = defaultdict(dict)
    for r in rows:
        items[r["item_id"]][r["annotator"]] = r["label"]
    annotators = sorted({a for v in items.values() for a in v})
    complete = [v for v in items.values() if len(v) == len(annotators)]
    rep.line(f"- Items: {len(items)}; annotators: {len(annotators)}; items rated by all: {len(complete)}")
    if len(annotators) >= 2:
        for a, b in combinations(annotators, 2):
            shared = [v for v in items.values() if a in v and b in v]
            if shared:
                k = cohen_kappa([v[a] for v in shared], [v[b] for v in shared])
                rep.line(f"- Cohen's κ {a}–{b}: {k:.3f} (n={len(shared)})")
    if len(annotators) > 2 and complete:
        fk = fleiss_kappa([[v[a] for a in annotators] for v in complete])
        rep.line(f"- Fleiss' κ (items rated by all): {fk:.3f}")
        rep.macro(f"{prefix}FleissKappa", f"{fk:.2f}")
    alpha = krippendorff_alpha({k: list(v.values()) for k, v in items.items()}, "nominal")
    rep.line(f"- Krippendorff's α (nominal): {alpha:.3f}")
    rep.macro(f"{prefix}KrippAlpha", f"{alpha:.2f}")


def section_rq2(rows, rep: Report, args) -> None:
    rep.h("RQ2: report ratings (W5)")
    dims = sorted({r["dimension"] for r in rows})
    raters = sorted({r["rater"] for r in rows})
    for d in dims:
        units = defaultdict(list)
        for r in rows:
            if r["dimension"] == d:
                units[(r["case_id"], r["system"])].append(float(r["score"]))
        a = krippendorff_alpha(units, "interval")
        rep.line(f"- Krippendorff's α (interval), {d}: {a:.3f}")
    all_units = defaultdict(list)
    for r in rows:
        all_units[(r["case_id"], r["system"], r["dimension"])].append(float(r["score"]))
    a_all = krippendorff_alpha(all_units, "interval")
    rep.line(f"- Krippendorff's α (interval), all dimensions pooled: {a_all:.3f} ({len(raters)} raters)")
    rep.macro("rqTwoAlpha", f"{a_all:.2f}")

    mean = defaultdict(list)
    for r in rows:
        mean[(r["case_id"], r["system"], r["dimension"])].append(float(r["score"]))
    mean = {k: statistics.mean(v) for k, v in mean.items()}
    ref = args.reference_system
    systems = sorted({k[1] for k in mean} - {ref})
    cases = sorted({k[0] for k in mean})
    raw = {}
    for d in dims:
        for s in systems:
            shared = [c for c in cases if (c, ref, d) in mean and (c, s, d) in mean]
            if shared:
                raw[(d, s)] = wilcoxon_signed_rank([mean[(c, ref, d)] for c in shared],
                                                   [mean[(c, s, d)] for c in shared])
    adj = holm(raw)
    rep.line("\n| Dimension | Baseline | p (raw) | p (Holm, all comparisons) |")
    rep.line("|---|---|---|---|")
    for (d, s), p in sorted(raw.items()):
        rep.line(f"| {d} | {s} | {p:.4f} | {adj[(d, s)]:.4f} |")
    n_sig = sum(1 for v in adj.values() if v < 0.05)
    rep.line(f"\n- Comparisons significant after Holm correction: {n_sig}/{len(adj)}")
    rep.macro("rqTwoHolmSig", f"{n_sig}/{len(adj)}")


def section_calls(rows, rep: Report) -> None:
    rep.h("LLM calls and tokens per case (W-B)")
    by = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by[r["system"]]["calls"].append(float(r["calls"]))
        by[r["system"]]["tokens"].append(float(r.get("prompt_tokens", 0) or 0) +
                                         float(r.get("completion_tokens", 0) or 0))
    rep.line("| System | cases | mean calls | median calls | mean tokens | median tokens |")
    rep.line("|---|---|---|---|---|---|")
    for s in sorted(by):
        c, t = by[s]["calls"], by[s]["tokens"]
        rep.line(f"| {s} | {len(c)} | {statistics.mean(c):.1f} | {statistics.median(c):.1f} | "
                 f"{statistics.mean(t):,.0f} | {statistics.median(t):,.0f} |")
        key = "".join(ch for ch in s if ch.isalnum())
        rep.macro(f"calls{key}", f"{statistics.mean(c):.1f}")
        rep.macro(f"tokens{key}", f"{statistics.mean(t):,.0f}".replace(",", "{,}"))


def section_calibration(rows, rep: Report) -> None:
    rep.h("Conformal calibration set (W4)")
    n = len({r["case_id"] for r in rows if r.get("role", "calibration") == "calibration"})
    rep.line(f"- Calibration cases: {n}")
    rep.macro("calibN", str(n))


# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rq1", type=Path, help="rq1_predictions.csv")
    ap.add_argument("--plre", type=Path, help="plre_predictions.csv")
    ap.add_argument("--annotations", type=Path, help="severity_annotations.csv (W-E)")
    ap.add_argument("--plre-annotations", type=Path, help="plre_annotations.csv (PLRE kappa)")
    ap.add_argument("--rq2", type=Path, help="rq2_ratings.csv")
    ap.add_argument("--calls", type=Path, help="llm_calls.csv")
    ap.add_argument("--calibration", type=Path, help="calibration_cases.csv")
    ap.add_argument("--reference-system", default="ALERT")
    ap.add_argument("--flat-system", default="ALERT-flat")
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=13)
    ap.add_argument("--out-dir", type=Path, default=Path("."))
    args = ap.parse_args()

    rep = Report()
    rep.md.append("# Review statistics\n")
    rep.md.append(f"Bootstrap resamples: {args.n_boot}; seed: {args.seed}; CIs are 95% percentile intervals.")

    if (rows := read_csv(args.rq1, ["case_id", "split", "label_source", "gold", "system", "pred"])) is not None:
        section_rq1(rows, rep, args)
    if (rows := read_csv(args.plre, ["pair_id", "archetype", "is_distractor", "gold", "system", "pred"])) is not None:
        section_plre(rows, rep, args)
    if (rows := read_csv(args.annotations, ["item_id", "annotator", "label"])) is not None:
        section_agreement(rows, rep, "Severity-label agreement (W-E)", "sev")
    if (rows := read_csv(args.plre_annotations, ["item_id", "annotator", "label"])) is not None:
        section_agreement(rows, rep, "PLRE-label agreement (W1)", "plre")
    if (rows := read_csv(args.rq2, ["case_id", "system", "rater", "dimension", "score"])) is not None:
        section_rq2(rows, rep, args)
    if (rows := read_csv(args.calls, ["case_id", "system", "calls"])) is not None:
        section_calls(rows, rep)
    if (rows := read_csv(args.calibration, ["case_id"])) is not None:
        section_calibration(rows, rep)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "review_stats.md").write_text("\n".join(rep.md) + "\n", encoding="utf-8")
    tex = ["% Generated by compute_review_stats.py -- paste into main.tex preamble."]
    tex += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in sorted(rep.tex.items())]
    (args.out_dir / "review_stats.tex").write_text("\n".join(tex) + "\n", encoding="utf-8")
    print(f"wrote {args.out_dir / 'review_stats.md'} and {args.out_dir / 'review_stats.tex'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
