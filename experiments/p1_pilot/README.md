# P1 pilot: reproduction

Pilot of Protocol P1 (paper App. I.1) on public data. Design: `DESIGN.md`
(frozen at commit `08aea76f`). Results: `RESULTS.md`, `RESULTS_TABLES.md`,
`results.json`.

## Steps

```bash
# 1. Data (public; not committed; checksums in checksums.txt)
mkdir -p data/raw
curl -L -o data/raw/GPO-CONAN-2022.pdf \
  https://www.govinfo.gov/content/pkg/GPO-CONAN-2022/pdf/GPO-CONAN-2022.pdf
pdftotext -layout data/raw/GPO-CONAN-2022.pdf data/raw/conan.txt
python cut_table.py data/raw/conan.txt data/raw/overruled_table.txt   # sha256 in checksums.txt
./download_cap.sh                   # CAP U.S. Reports volumes 1-572 (CC0)

# 2. Pipeline
python parse_conan.py               # -> data/pairs_raw.csv   (282 pairs)
python build_corpus.py              # -> data/work/corpus.jsonl
python match_cases.py               # -> data/pairs.csv, data/pairs_excluded.csv
python build_queries.py             # -> data/work/queries.jsonl
python retrieve.py --host bm25
./run_dense.sh                      # bge (2 chunks) and legalbert (1 chunk), CPU
python evaluate.py                  # -> results.json (10,000 bootstrap resamples)
python report.py                    # -> RESULTS_TABLES.md
python sensitivity.py               # post-hoc sensitivity (not pre-specified) -> sensitivity.json

# 3. Tests
python -m unittest test_p1.py
```

Requirements: Python 3.10+, `numpy scipy scikit-learn torch transformers`
(CPU is enough), `pdftotext` (poppler).

`data/pairs_raw.csv`, `data/pairs.csv` and `data/pairs_excluded.csv` are
committed; raw downloads, the corpus, embeddings and runs are not.

The released testbed built from this pilot (queries, qrels, gold closures and a
standalone scorer for any TREC run) is in `benchmarks/scotus_overruled/`.
