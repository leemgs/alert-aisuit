# P1 pilot: supersession-aware retrieval on overruled U.S. Supreme Court precedent

**Status:** design only. Nothing has been run. Freeze this file (record its git
commit hash, optionally deposit it on OSF) **before** any retrieval run, so the
analysis cannot be tuned after seeing results.

**Relation to the paper:** this is a *pilot* of Protocol P1 (App. I.1), not P1
itself. It uses public data that can be obtained without licences, and it
deviates from P1 in the ways listed in §9. It may be reported as
"P1 pilot (slice b only)"; it must not be reported as "P1 executed".

---

## 1. Question

Does applying validity intervals at retrieval time, as an add-on re-scoring layer,
help retrievers that know nothing about ALERT (no agent loop, no ALERT data, no
goal predicate) when the corpus contains authority that was later overruled?

Two sub-questions, kept separate:

- **Q1 (prevalence):** how often do standard retrievers put an already-overruled
  case in their top-k? If they rarely do, the gate cannot matter much on any
  corpus.
- **Q2 (effect):** given validity intervals, how much does the gate change
  retrieval quality, and does it hurt where nothing was overruled?

## 2. Data (all public)

| Role | Source | Licence / access |
|---|---|---|
| Gold closures | *Table of Supreme Court Decisions Overruled by Subsequent Decisions*, Constitution Annotated (constitution.congress.gov). The Library of Congress has counted about 232 overrulings since 1810. | U.S. government work |
| Corpus and citing contexts | U.S. Supreme Court opinions from the Caselaw Access Project (case.law), with decision dates and parsed citations | CC0; commercial restrictions ended March 2024 |
| Fallback corpus | CourtListener bulk data (opinions and citation graph) | free bulk download; the REST API is too rate-limited (about 125 requests/day) for this volume |
| Extractor sanity check (optional) | RegLab/Casetext *Overruling* sentence dataset (2,400 sentences) | check licence before use |

**Gold closure for each table entry:** the overruled case `A` gets interval end
`e_A` = decision date of the overruling case `B`. Entries marked as overruled
"in part" go to a separate *partial* stratum (§5).

**Exclusions, fixed in advance:**
- Overrulings decided on or after 2020-01-01 are excluded, so the pilot is
  disjoint from the ALERT-Dataset window (2020–2025). This removes, for example,
  *Ramos v. Louisiana* (2020), *Dobbs* (2022) and *Loper Bright* (2024).
- Entries whose `A` or `B` cannot be matched unambiguously to a CAP case are
  dropped and listed.

## 3. Queries: citing contexts with the citation masked

Queries are taken from later opinions that cite the cases, so relevance labels
come from what judges actually cited, not from annotators or an LLM.

For each gold pair (A overruled by B on date t):

- **Pre-closure queries:** passages from opinions decided *before* t that cite A.
  Query date `t_q` is the citing opinion's decision date. Gold relevant: A.
- **Post-closure queries:** passages from opinions decided *after* t that cite B
  for the point on which B overruled A. Gold relevant: B. A is **stale**: it
  counts as non-relevant, and retrieving it counts toward the stale rate.
- **No-stale control queries:** passages citing Supreme Court cases that appear
  nowhere in the overruled table, sampled to match the citing years of the
  post-closure queries. These test non-inferiority (§6).

**Query construction:**
- Passage = the sentence containing the citation plus one sentence on each side.
- Mask every case name, reporter citation, and year in the passage.
- Drop post-closure passages that also mention A or contain explicit overruling
  language ("overrul", "abrogat", "no longer good law"), so queries do not give
  away the answer.
- At most 5 queries per pair and per role (pre/post), chosen with a fixed random
  seed, so that heavily cited pairs do not dominate.

**Target size:** at least 150 pairs with at least one post-closure query; about
500–750 queries in total, plus an equal number of control queries.

## 4. Host retrievers (unmodified, as in P1)

1. **BM25** over full opinions (Pyserini, default parameters).
2. **General dense encoder:** an open `e5`/`bge` model, with opinions split into
   512-token chunks and the opinion score taken as the maximum chunk score.
3. **Legal encoder:** LegalBERT with mean pooling, chunked the same way.

Each host retrieves its top 100 for every query. The gate only re-scores this
list, so no index is rebuilt (as P1 specifies).

## 5. Conditions

For every host and every query:

| Condition | Score |
|---|---|
| ungated | `score_host` |
| + indicator | `score_host × 1[s_v ≤ t_q < e_v]` |
| + indicator + weight | `score_host × 1[·] × w(treat)` |

- Full overrulings are already removed by the indicator, so the weight only
  affects the *partial* stratum. The paper's exact `w(·)` must be used if the
  authors provide it. If not, report a sensitivity sweep over
  `w_partial ∈ {0.25, 0.5, 0.75}` and say that ALERT's schedule was unavailable.
- **Treatment-label variants (P1's confound control):**
  - *gold-treatment:* intervals from the Constitution Annotated table;
  - *extractor-treatment:* intervals produced by ALERT's own edge extractor run
    on the opinions in the corpus. This needs the authors' extractor; without it
    the pilot reports gold-treatment only and says so.

## 6. Metrics and statistics (as in P1, with one stricter change)

- **Metrics:** nDCG@10, Recall@10, MRR, and stale rate@10, computed on
  post-closure queries as the share of queries whose top 10 contains A.
- **Primary endpoints:** paired deltas (gated − ungated) per host.
- **Resampling:** paired bootstrap with 10,000 resamples and 95% CIs, **clustered
  by gold pair**, because queries from the same pair are not independent.
  Clustering is stricter than P1's per-query bootstrap; also report the per-query
  version.
- **Multiple testing:** Holm correction across the three hosts.
- **Non-inferiority:** on control queries, the nDCG@10 delta must have a lower
  95% bound above −0.5 points.
- **Sanity check (must hold exactly):** on pre-closure queries the gate never
  removes A. Any violation is a bug, not a result.

## 7. Acceptance criteria (adapted from P1, fixed now)

The pilot **supports transfer** if, on gold-treatment intervals:
1. nDCG@10 improves and stale rate@10 falls significantly (Holm-adjusted) for at
   least two of the three hosts; and
2. non-inferiority holds on control queries for those hosts.

Report the extractor-treatment variant with the same criteria whenever it is
available. Report every outcome, including failure.

## 8. What the result can and cannot show

- With **gold** intervals, the gate can only remove authority that really was
  overruled. The gain is therefore close to an upper bound, and it is non-zero
  only to the extent that hosts actually retrieve stale cases. Q1 (prevalence)
  is the informative number here: it shows whether the problem the paper
  addresses occurs in standard retrievers.
- The **extractor** variant is the realistic test: missed closures leave stale
  cases in, and false closures can hurt control queries.
- A positive pilot supports "the gate helps external retrievers on U.S. Supreme
  Court overrulings". It does not cover lower courts, partial treatments such as
  "narrowed", other domains, or the full P1.

## 9. Deviations from pre-specified P1 (report all of them)

| P1 says | Pilot does | Why |
|---|---|---|
| (a) COLIEE-style public benchmark | not run | COLIEE requires a signed memorandum and uses Canadian case law without supersession labels |
| (b) temporally held-out CourtListener slice | U.S. Supreme Court opinions from CAP/CourtListener, overrulings before 2020 | public, licence-free gold closures exist only at this level |
| per-query bootstrap | cluster bootstrap by pair (per-query also reported) | queries from the same pair are correlated |
| treatment weight `w(·)` from ALERT | ALERT's `w` if provided, otherwise a sweep | the paper does not state `w` |
| gold labels "gold/citator-derived" | Constitution Annotated table | independent, authoritative, public |

## 10. Implementation plan

```
experiments/p1_pilot/
  fetch_conan.py        # download and parse the overruled table -> pairs.csv
  build_corpus.py       # CAP/CourtListener SCOTUS opinions -> corpus.jsonl (id, date, text)
  match_cases.py        # match table entries to corpus ids; log unmatched entries
  build_queries.py      # citing contexts -> queries.jsonl (masked, with t_q, role, pair)
  retrieve.py           # BM25 / dense / legal top-100 per query -> runs/*.trec
  gate.py               # apply indicator (+ weight) -> gated runs
  evaluate.py           # metrics, clustered paired bootstrap, Holm, NI -> results.md
  test_*.py             # unit tests: masking, gate never fires before t, metric correctness
```

- **Compute:** BM25 runs on a CPU. Encoding about 30,000 opinions in chunks takes
  hours on a CPU with a base-size encoder, and much less on one GPU.
- **Reproducibility:** fixed seeds; every intermediate file is checksummed; the
  frozen design hash is recorded in `results.md`.

## 11. Responsible conduct

- All inputs are public court records or government works. There are no human
  subjects.
- If the pilot is run with help from an AI assistant, the paper must say so (the
  Ethics Statement's AI-assistant paragraph and checklist item E1 would then
  cover experiment code, not only text editing), and the authors should re-run
  `evaluate.py` themselves before reporting.
- Results go into App. I.1 as a pilot. Limitations ("Generality is untested") is
  updated in either direction, and a negative result is reported as such.

## Sources checked while writing this design

- Constitution Annotated, overruled-decisions table: <https://constitution.congress.gov> (count of about 232: <https://constitutioncenter.org/amp/blog/a-short-list-of-overturned-supreme-court-landmark-decisions>)
- Caselaw Access Project licence and end of commercial restrictions: <https://www.lawnext.com/2024/03/event-tomorrow-marks-the-end-of-commercial-restrictions-on-the-caselaw-access-project-that-digitized-all-u-s-case-law.html>
- CourtListener bulk data: <https://wiki.free.law/c/courtlistener/help/api/bulk-data/bulk-legal-data>; API rate limits: <https://wiki.free.law/c/courtlistener/help/api/rest/faqs/my-api-key-appears-to-be-throttled-rate-limited-help>
- Overruling sentence dataset: <https://reglab.stanford.edu/data/the-overruling-dataset-a-benchmark-for-detecting-legal-decisions-that-have-been-overruled/>
- COLIEE case-law task and memorandum: <https://sites.ualberta.ca/~rabelo/COLIEE2023/>
- Related: LePaRD (judicial citation contexts, ACL 2024) <https://aclanthology.org/2024.acl-long.532/>; precedent-treatment classification (NLLP 2025) <https://arxiv.org/pdf/2605.17691>
