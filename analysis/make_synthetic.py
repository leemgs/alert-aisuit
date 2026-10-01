#!/usr/bin/env python3
"""Write small synthetic input files in the exact format compute_review_stats.py expects.

Used by the tests and as a worked example of the input formats. The numbers are
random and mean nothing.
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

LABELS = ["High", "Medium", "Low"]
SYSTEMS_RQ1 = ["B1", "B2", "B3", "B4", "B5", "ALERT", "ALERT-noGoalChecker"]
SYSTEMS_PLRE = ["cosine", "LegalBERT-NLI", "COLIEE-retrieval", "RAG-only", "ALERT-flat", "ALERT"]


def noisy(rng, gold, acc, choices):
    return gold if rng.random() < acc else rng.choice([c for c in choices if c != gold])


def write(path: Path, header: list[str], rows: list[list]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def main(out: Path, seed: int = 0) -> None:
    rng = random.Random(seed)
    out.mkdir(parents=True, exist_ok=True)

    # RQ1: 200 cases, 60 human-adjudicated
    rows = []
    for i in range(200):
        split = rng.choices(["train", "validation", "test"], [0.7, 0.1, 0.2])[0]
        source = "human" if i < 60 else "retained"
        gold = rng.choice(LABELS)
        for k, s in enumerate(SYSTEMS_RQ1):
            acc = 0.55 + 0.05 * k if s != "ALERT-noGoalChecker" else 0.75
            rows.append([f"c{i}", split, source, gold, s, noisy(rng, gold, acc, LABELS)])
    write(out / "rq1_predictions.csv", ["case_id", "split", "label_source", "gold", "system", "pred"], rows)

    # PLRE: 300 pairs over 5 archetypes
    rows = []
    for i in range(300):
        split = "test" if i % 3 == 0 else "train"
        distr = 1 if rng.random() < 0.2 else 0
        gold = 0 if distr else int(rng.random() < 0.4)
        for k, s in enumerate(SYSTEMS_PLRE):
            acc = 0.6 + 0.05 * k
            if s == "ALERT-flat" and distr:
                acc = 0.4
            pred = gold if rng.random() < acc else 1 - gold
            stale = int(distr and pred == 1)
            rows.append([f"p{i}", f"c{i % 50}", f"A{i % 5}", split, distr, gold, s, pred, stale])
    write(out / "plre_predictions.csv",
          ["pair_id", "case_id", "archetype", "split", "is_distractor", "gold", "system", "pred", "stale_cite"], rows)

    # Severity annotations: 3 annotators x 80 items
    rows = []
    for i in range(80):
        gold = rng.choice(LABELS)
        for a in ("ann1", "ann2", "ann3"):
            rows.append([f"c{i}", a, noisy(rng, gold, 0.8, LABELS)])
    write(out / "severity_annotations.csv", ["item_id", "annotator", "label"], rows)

    # RQ2: 15 cases x 5 systems x 2 raters x 5 dimensions
    rows = []
    dims = ["Accuracy", "Completeness", "Actionability", "EvidenceSufficiency", "Clarity"]
    for c in range(15):
        for k, s in enumerate(["B2", "B3", "B4", "B5", "ALERT"]):
            for d in dims:
                base = 3 + 0.25 * k
                for r in ("r1", "r2"):
                    rows.append([f"c{c}", s, r, d, max(1, min(5, round(base + rng.gauss(0, 0.7))))])
    write(out / "rq2_ratings.csv", ["case_id", "system", "rater", "dimension", "score"], rows)

    # LLM calls
    rows = []
    for c in range(40):
        rows.append([f"c{c}", "ALERT", rng.randint(6, 14), rng.randint(8000, 20000), rng.randint(800, 2000)])
        rows.append([f"c{c}", "B5", rng.randint(2, 4), rng.randint(3000, 7000), rng.randint(400, 900)])
    write(out / "llm_calls.csv", ["case_id", "system", "calls", "prompt_tokens", "completion_tokens"], rows)

    write(out / "calibration_cases.csv", ["case_id"], [[f"cal{i}"] for i in range(125)])


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "synthetic"))
