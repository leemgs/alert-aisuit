# SCOTUS-Overruled: a testbed for supersession-aware retrieval

When a later decision overrules an earlier one, the earlier opinion is often
still textually similar to new queries. A retriever that ranks it highly hands
a generator authority that is no longer good law. This testbed measures how
often that happens and whether a retrieval-time validity gate helps, using
only public, licence-free U.S. Supreme Court data.

It is the data of the P1 pilot in the ALERT paper (App. I.1). It is released so
others can test their own retrievers, gates and treatment extractors on the same
queries and gold closures.

## What is in it

| File | Content |
|---|---|
| `data/queries.jsonl` | 3,327 masked citing-context queries: `qid`, `set`, query date `t_q`, `text`, `exclude_doc` (the source opinion), `pair`, `gold_closed_at_tq` |
| `data/qrels.tsv` | TREC qrels: one relevant document per query |
| `data/stale.tsv` | `qid`, overruled case A for post-closure queries |
| `data/closures.tsv` | gold validity-interval ends: earliest full and partial overruling date per document |
| `data/corpus_ids.tsv` | the 29,030 opinions in the corpus (`doc_id`, decision date, citation, name) |
| `data/pairs.csv`, `pairs_excluded.csv` | the 253 overruled/overruling pairs used, and the 29 excluded with reasons |
| `make_corpus.py` | builds `data/docs.jsonl` (full opinion text) from the CAP download |
| `score.py` | scores any TREC run, optionally gated; paired deltas with a cluster bootstrap |
| `test_score.py` | sanity tests (`python -m unittest test_score.py`) |
| `SHA256SUMS` | checksums of the data files |

### Query sets

| Set | n | Query cites | Gold | Stale |
|---|---|---|---|---|
| `post_full` | 984 (208 pairs) | the overruling case B, after a full overruling | B | the overruled case A |
| `post_part` | 149 | B, after a partial overruling | B | A |
| `pre` | 1,061 | A, before its first full overruling | A | — |
| `control` | 1,133 | a case not in the overruled table (matched on citing decade) | that case | — |

Queries are the citing sentence plus one sentence on each side, with case names,
reporter citations and years masked (`[CASE]`, `[CITE]`, `[YEAR]`). Post-closure
passages that mention A, its parties or overruling language are dropped.

### Rules

A system may retrieve, for query `q`, only opinions decided **strictly before**
`q.t_q` and different from `q.exclude_doc`. `score.py` drops anything else and
warns. Gold closures come from `closures.tsv` and are never inferred from the
query text.

## Sources and licence

- Gold closures: *Table of Supreme Court Decisions Overruled by Subsequent
  Decisions*, Constitution Annotated, 2022 edition (GPO-CONAN-2022; U.S.
  government work).
- Opinions: Caselaw Access Project, U.S. Reports volumes 1–572 (CC0), covering
  decisions up to 2014. Overrulings decided in or after 2020 are excluded.
- Derived files in this folder: CC BY 4.0; code: MIT.

## Build the corpus

```bash
cd ../../experiments/p1_pilot
./download_cap.sh && python build_corpus.py      # about 1.2 GB download, CPU only
cd ../../benchmarks/scotus_overruled
python make_corpus.py ../../experiments/p1_pilot/data/work/corpus.jsonl
```

## Score a run

```bash
python score.py my_run.trec                                   # ungated
python score.py my_run.trec --gate indicator --baseline my_run.trec   # gate effect
```

Metrics: nDCG@10 (×100), Recall@10, MRR, stale@10 (queries with A in the top 10)
and stale-any@10 (share of the top 10 already fully overruled at `t_q`).

## Reference results

Top 100 per query, gold-closure indicator gate, `post_full` set. Reproduce with
`experiments/p1_pilot/retrieve.py` and `score.py`. bge uses only the first
2 × 512 tokens of each opinion and LegalBERT only the first 512 (CPU budget), so
both dense numbers are lower bounds for those models.

| Host | nDCG@10 ungated → gated | R@10 | MRR | stale@10 ungated → gated |
|---|---|---|---|---|
| BM25 (k1 0.9, b 0.4) | 28.88 → 28.97 | 42.0% | 0.258 | 8.3% → 0.0% |
| bge-small-en-v1.5 | 8.35 → 8.47 | 14.3% | 0.072 | 5.5% → 0.0% |
| LegalBERT (mean pooling) | 2.30 → 2.30 | 4.4% | 0.020 | 0.4% → 0.0% |

Control-set nDCG@10 (ungated): BM25 25.70, bge 8.33, LegalBERT 1.79. The gate
never removed the gold case on `pre` queries.

## Known issues

- Four `post_full` queries (`gold_closed_at_tq: true`) have a gold case B that
  was itself overruled before `t_q` (*Rabinowitz*, overruled by *Chimel*, 1969).
  A correct gate removes the gold case there. Report results with and without
  them (`--exclude-gold-closed`).
- Post-closure queries cite B on *any* point, not necessarily the overruled one.
- Masking removes names, citations and years but not pin-cite page numbers.
- Coverage is the U.S. Supreme Court only, with decisions up to 2014. Lower courts,
  statutes and partial treatments such as "narrowed" or "questioned" are not
  covered.

## Open problems this testbed can support

1. **Extractor-treatment variant.** Replace `closures.tsv` with closures predicted
   by a treatment extractor run on `docs.jsonl`, and measure what extraction
   errors cost relative to gold closures.
2. **Stronger hosts.** Use full-document dense retrieval, re-rankers and learned
   sparse models. The gate can only help when stale authority outranks the
   correct authority, so prevalence (stale@10 ungated) is the first thing to
   measure.
3. **Soft versus hard gating.** Compare removal with down-weighting for partial
   overrulings. In the pilot, w in {0.25, 0.5, 0.75} produced identical rankings.
4. **Generation.** Measure whether gating changes which authority an LLM cites
   when it answers from the top-k.
