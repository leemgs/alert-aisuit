"""Sanity tests for score.py on the released data (python -m unittest test_score.py)."""

import json
import tempfile
import unittest
from argparse import Namespace

import score


class ScoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.queries, cls.gold, cls.stale, cls.dates, cls.full, cls.part = score.load()

    def run_for(self, ranking):
        with tempfile.NamedTemporaryFile("w", suffix=".trec", delete=False) as f:
            for qid, docs in ranking.items():
                for r, d in enumerate(docs):
                    f.write(f"{qid} Q0 {d} {r + 1} {100 - r} t\n")
        run, dropped = score.admissible(score.read_run(f.name), self.queries, self.dates)
        return run, dropped

    def args(self, gate="none"):
        return Namespace(gate=gate, w=0.5, exclude_gold_closed=False)

    def test_gold_is_always_admissible(self):
        for qid, q in self.queries.items():
            g = self.gold[qid]
            self.assertLess(self.dates[g], q["t_q"])
            self.assertNotEqual(g, q["exclude_doc"])

    def test_perfect_run(self):
        run, dropped = self.run_for({q: [self.gold[q]] for q in self.queries})
        self.assertEqual(dropped, 0)
        s = score.summarize(score.per_query(run, self.queries, self.gold, self.stale, self.full, self.part, self.args()),
                            self.queries)
        for v in s.values():
            self.assertAlmostEqual(v["ndcg@10"], 100.0)

    def test_gate_removes_stale_on_post_full(self):
        ids = [q for q, v in self.queries.items() if v["set"] == "post_full"]
        run, _ = self.run_for({q: [self.stale[q], self.gold[q]] for q in ids})
        pq = score.per_query(run, {q: self.queries[q] for q in ids}, self.gold, self.stale, self.full, self.part,
                             self.args("indicator"))
        self.assertTrue(all(m["stale@10"] == 0.0 for m in pq.values()))

    def test_future_documents_are_dropped(self):
        q = next(iter(self.queries))
        later = next(d for d, dt in self.dates.items() if dt >= self.queries[q]["t_q"])
        _, dropped = self.run_for({q: [later, self.gold[q]]})
        self.assertEqual(dropped, 1)


if __name__ == "__main__":
    unittest.main()
