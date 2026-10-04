"""Unit tests for the P1 pilot (python -m unittest test_p1.py)."""

import unittest

from evaluate import bootstrap, gate, holm
from p1lib import mask, mrr, ndcg_at, passage_around, recall_at, split_sentences
from parse_conan import parse

TABLE = """
            Overruling                 Overruling               Overruled                  Overruled
Dobbs v. Jackson Women's Health           2022      Planned Parenthood of Southeastern        1992
Organization,                                       Pennsylvania v. Casey,
No. 19-1391 (U.S. June 24, 2022)                    505 U.S. 833 (1992);
                                                    Roe v. Wade,                              1973
                                                    410 U.S. 113 (1973)
The Belfast,                              1869      Allen v. Newberry,                     1858
74 U.S. (7 Wall.) 624 (1869)                        62 U.S. (21 How.) 244 (1858) (in
                                                    part)
""".splitlines()


class ParseTests(unittest.TestCase):
    def test_parse_rows(self):
        rows = parse(TABLE)
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["overruled_cite"], "505 U.S. 833")
        self.assertEqual(rows[1]["overruled_name"], "Roe v. Wade")
        self.assertEqual(rows[1]["overruled_year"], 1973)
        self.assertEqual(rows[2]["overruling_cite"], "74 U.S. 624")
        self.assertEqual(rows[2]["overruled_cite"], "62 U.S. 244")
        self.assertEqual(rows[2]["partial"], 1)
        self.assertEqual(rows[0]["partial"], 0)


class TextTests(unittest.TestCase):
    def test_mask_removes_cites_years_and_case_names(self):
        s = "See Miranda v. Arizona, 384 U. S. 436, 444 (1966); Escobedo, 378 U.S. 478."
        m = mask(s, ["Escobedo"])
        self.assertNotIn("384", m)
        self.assertNotIn("1966", m)
        self.assertNotIn("Miranda", m)
        self.assertNotIn("Escobedo", m)
        self.assertIn("[CITE]", m)

    def test_sentence_split_protects_abbreviations(self):
        t = "The Court in Smith v. Jones, 1 U. S. 1, held so. Later cases agreed. Id. at 5."
        spans = split_sentences(t)
        first = t[spans[0][0]:spans[0][1]]
        self.assertIn("held so.", first)
        self.assertIn("Smith v. Jones", first)

    def test_passage_has_neighbours(self):
        t = "Alpha one. Beta two cites 9 U. S. 9 here. Gamma three. Delta four."
        p = passage_around(t, t.index("9 U. S."))
        self.assertTrue(p.startswith("Alpha") and p.endswith("three."))


class GateTests(unittest.TestCase):
    full = {1: "1990-01-01"}
    part = {2: "1990-01-01"}
    docs = [[1, 0.9], [2, 0.8], [3, 0.1]]

    def test_gate_never_fires_before_closure(self):
        self.assertEqual(gate(self.docs, "1989-12-31", self.full, self.part), [1, 2, 3])

    def test_gate_removes_at_and_after_closure(self):
        self.assertEqual(gate(self.docs, "1990-01-01", self.full, self.part), [2, 3])
        self.assertEqual(gate(self.docs, "2000-05-05", self.full, self.part), [2, 3])

    def test_weight_only_affects_partial_after_closure(self):
        self.assertEqual(gate(self.docs, "1995-01-01", self.full, self.part, w=0.01), [3, 2])
        self.assertEqual(gate(self.docs, "1985-01-01", self.full, self.part, w=0.01), [1, 2, 3])


class MetricTests(unittest.TestCase):
    def test_metrics(self):
        r = [5, 7, 9]
        self.assertAlmostEqual(ndcg_at(r, 7), 1 / 1.584962500721156, places=9)
        self.assertEqual(recall_at(r, 9), 1.0)
        self.assertEqual(recall_at(r, 4), 0.0)
        self.assertAlmostEqual(mrr(r, 9), 1 / 3)

    def test_bootstrap_and_holm(self):
        d = {i: (f"p{i % 20}", 1.0 + (i % 3) * 0.1) for i in range(100)}
        mean, lo, hi, p = bootstrap(d, True, 500)
        self.assertGreater(lo, 0.9)
        self.assertLess(p, 0.01)
        adj = holm({"a": 0.01, "b": 0.04, "c": 0.03})
        self.assertAlmostEqual(adj["a"], 0.03)
        self.assertAlmostEqual(adj["b"], 0.06)


if __name__ == "__main__":
    unittest.main()
