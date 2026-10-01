"""Tests for compute_review_stats.py.

Metric implementations are checked against reference libraries when they are
installed (scikit-learn, statsmodels, krippendorff, scipy); those checks are
skipped otherwise. An end-to-end run on synthetic data is always tested.

    python -m unittest test_compute_review_stats.py
"""

from __future__ import annotations

import random
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import compute_review_stats as crs  # noqa: E402
import make_synthetic  # noqa: E402


def _have(mod: str) -> bool:
    try:
        __import__(mod)
        return True
    except ImportError:
        return False


class MetricTests(unittest.TestCase):
    def setUp(self):
        rng = random.Random(1)
        self.labels = ["H", "M", "L"]
        self.gold = [rng.choice(self.labels) for _ in range(300)]
        self.pred = [g if rng.random() < 0.7 else rng.choice(self.labels) for g in self.gold]

    @unittest.skipUnless(_have("sklearn"), "scikit-learn not installed")
    def test_macro_prf_matches_sklearn(self):
        from sklearn.metrics import precision_recall_fscore_support

        p, r, f, _ = precision_recall_fscore_support(self.gold, self.pred, average="macro", zero_division=0)
        mp, mr, mf = crs.macro_prf(self.gold, self.pred)
        self.assertAlmostEqual(mp, p, places=10)
        self.assertAlmostEqual(mr, r, places=10)
        self.assertAlmostEqual(mf, f, places=10)

    @unittest.skipUnless(_have("sklearn"), "scikit-learn not installed")
    def test_binary_prf_and_cohen_match_sklearn(self):
        from sklearn.metrics import cohen_kappa_score, f1_score

        g = [1 if x == "H" else 0 for x in self.gold]
        p = [1 if x == "H" else 0 for x in self.pred]
        self.assertAlmostEqual(crs.binary_prf(g, p)[2], f1_score(g, p), places=10)
        self.assertAlmostEqual(crs.cohen_kappa(self.gold, self.pred),
                               cohen_kappa_score(self.gold, self.pred), places=10)

    @unittest.skipUnless(_have("statsmodels"), "statsmodels not installed")
    def test_fleiss_matches_statsmodels(self):
        from statsmodels.stats.inter_rater import aggregate_raters, fleiss_kappa

        rng = random.Random(2)
        table = [[rng.choice(self.labels) for _ in range(3)] for _ in range(100)]
        counts, _ = aggregate_raters([[self.labels.index(x) for x in row] for row in table])
        self.assertAlmostEqual(crs.fleiss_kappa(table), fleiss_kappa(counts), places=10)

    @unittest.skipUnless(_have("krippendorff"), "krippendorff not installed")
    def test_krippendorff_matches_reference(self):
        import krippendorff
        import numpy as np

        rng = random.Random(3)
        n_items, n_raters = 60, 3
        data = [[rng.randint(1, 5) if rng.random() > 0.1 else None for _ in range(n_items)]
                for _ in range(n_raters)]
        arr = np.array([[np.nan if v is None else v for v in row] for row in data], dtype=float)
        units = {i: [data[r][i] for r in range(n_raters) if data[r][i] is not None] for i in range(n_items)}
        for level in ("nominal", "interval"):
            ref = krippendorff.alpha(reliability_data=arr, level_of_measurement=level)
            self.assertAlmostEqual(crs.krippendorff_alpha(units, level), ref, places=8)

    def test_wilcoxon_fallback_close_to_scipy(self):
        rng = random.Random(4)
        x = [rng.gauss(3.5, 0.5) for _ in range(15)]
        y = [v - 0.4 + rng.gauss(0, 0.3) for v in x]
        p = crs.wilcoxon_signed_rank(x, y)
        self.assertTrue(0 <= p <= 1)
        if _have("scipy"):
            from scipy.stats import wilcoxon

            self.assertAlmostEqual(p, wilcoxon(x, y).pvalue, places=10)

    def test_holm(self):
        adj = crs.holm({"a": 0.01, "b": 0.04, "c": 0.03})
        self.assertAlmostEqual(adj["a"], 0.03)
        self.assertAlmostEqual(adj["c"], 0.06)
        self.assertAlmostEqual(adj["b"], 0.06)

    def test_paired_bootstrap_detects_clear_difference(self):
        items = list(range(200))
        good = {i: 1 for i in items}
        bad = {i: (1 if i % 2 else 0) for i in items}
        d, (lo, hi), p = crs.paired_bootstrap(items, lambda s: sum(good[i] for i in s) / len(s),
                                              lambda s: sum(bad[i] for i in s) / len(s), 2000, 0)
        self.assertGreater(d, 0.4)
        self.assertGreater(lo, 0)
        self.assertLess(p, 0.01)


class EndToEndTest(unittest.TestCase):
    def test_synthetic_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            make_synthetic.main(tmp / "in")
            out = tmp / "out"
            cmd = [sys.executable, str(HERE / "compute_review_stats.py"),
                   "--rq1", str(tmp / "in/rq1_predictions.csv"),
                   "--plre", str(tmp / "in/plre_predictions.csv"),
                   "--annotations", str(tmp / "in/severity_annotations.csv"),
                   "--rq2", str(tmp / "in/rq2_ratings.csv"),
                   "--calls", str(tmp / "in/llm_calls.csv"),
                   "--calibration", str(tmp / "in/calibration_cases.csv"),
                   "--n-boot", "300", "--out-dir", str(out)]
            subprocess.run(cmd, check=True, capture_output=True)
            md = (out / "review_stats.md").read_text()
            tex = (out / "review_stats.tex").read_text()
            for heading in ("RQ1", "PLRE", "Severity-label agreement", "RQ2", "LLM calls", "calibration"):
                self.assertIn(heading, md)
            self.assertIn("without stale-authority distractors", md)
            self.assertIn("Per-archetype", md)
            self.assertIn("Calibration cases: 125", md)
            for line in tex.splitlines()[1:]:
                self.assertRegex(line, r"^\\newcommand\{\\[A-Za-z]+\}\{.*\}$")
            self.assertIn("\\calibN}{125}", tex)
            self.assertTrue(re.search(r"\\callsBFive\}\{\d", tex))


if __name__ == "__main__":
    unittest.main()
