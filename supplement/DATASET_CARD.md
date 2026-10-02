# ALERT-Dataset: dataset card

Structured after *Datasheets for Datasets* and *Data Statements for NLP*. Every
statement below is taken from the paper; items marked **TODO** need information
that the paper does not contain and must be filled in before release.

## Summary

ALERT-Dataset is a curated set of U.S. federal litigation involving AI systems
(mainly copyright and other intellectual-property claims), built for structured
legal-risk analysis and for the Product–Litigation Risk Entailment (PLRE) task.

| Property | Value |
|---|---|
| Cases (dockets) | 1,247 (1,260 raw records before deduplication) |
| Documents | 8,934 |
| Coverage | January 2020 – December 2025, concentrated in 2023–2025 |
| Jurisdiction / language | U.S. federal courts; English |
| Unique defendants | 43 (top three account for 41.3% of cases) |
| Record schema | 22 fields (paper Table A.1) |
| Severity labels | 3 classes: High (critical + high merged), Medium, Low |
| Status (initiated/active/settled/dismissed) | 298 / 695 / 148 / 106 |
| Product-mapping cases (PLRE) | 312, over 5 anonymized product archetypes |
| Treatment graph | 1,812 nodes, 4,760 treatment edges |
| Splits | 70 / 10 / 20 train / validation / test, stratified by year and litigation type |
| License | CC BY 4.0 (code: MIT) |

## Motivation

Engineering teams building generative-AI products need to know whether a
product attribute is exposed to a legal-risk theory under authority that is
still valid at a given date. Existing legal NLP datasets take legal text as the
premise and treat the corpus as static; this dataset links product attributes,
legal-risk theories, query dates, and time-valid authority.

## Composition

- **Unit:** one case is one docket. Consolidated or related actions are *not*
  merged, so a dispute litigated across several dockets appears several times.
- **Record fields:** docket metadata (case number and title, filing date, docket
  number, court, jurisdiction, status, last update), parties and counsel,
  alleged training data and implicated product, cause of action, claimed
  damages, an AI-generated case summary (human-verified), a chronological
  history log, progress notes, and source/tracker URLs.
- **Labels:** severity label per case; per-record label provenance (human-adjudicated or retained automated pre-label).
- **PLRE pairs:** directional (product attribute, legal-risk theory, query date)
  triples labeled positive only when at least one valid supporting authority
  exists at the query date; negatives include ordinary mismatches and
  stale-authority distractors. **TODO:** number of pairs, positive rate,
  distractor share (computable with `analysis/compute_review_stats.py`).
- **Personal information:** names of parties and counsel as they appear in
  public court filings. No other personal information is collected.
- **Not included:** attorney-authored complaint text beyond what is already
  public; news article text (news items appear only as links and derived
  metadata); proprietary citator content.

## Collection

- Candidate dockets were found by retrospective keyword search of RECAP
  complaint, amended-complaint, and petition entries on CourtListener, combining
  AI-training terms, legal-theory terms, and data-source terms. Legal-news
  signals were used only to locate dockets.
- A reviewer kept a docket only if the complaint puts the development,
  training, or deployment of an AI system at issue.
- Litigation type (copyright, DMCA, trade secret, other) was assigned afterwards
  from the recorded cause of action.

## Annotation

- An automated rule-based pre-labeler (paper Table A.3) assigned an initial
  triage score to every case.
- Three legal research specialists independently reviewed a stratified sample
  of 400 cases under a fixed guideline, without seeing system identity or the
  pre-labeler's score; Cohen's κ = 0.74.
- The other 847 cases keep the automated pre-label; a 5% spot-check found 91%
  agreement with at least one specialist (a lenient criterion).
- Annotators are staff of the authors' institution, working within their
  regular paid duties; they were told how annotations would be used and agreed
  verbally. No formal ethics-board review was sought.
- **TODO:** link to the annotation guideline document; PLRE-label agreement.

## Uses

- **Intended:** research on legal-risk analysis, time-aware retrieval, and
  product-conditioned legal entailment; decision support for qualified reviewers.
- **Out of scope:** automated legal decisions, legal advice, predicting
  litigation outcomes. Severity labels are triage proxies, not findings of liability.

## Known limitations and biases

- Skewed toward the largest defendants; limited coverage of smaller vendors.
- U.S. federal courts and English only.
- Per-docket counting over-represents multi-docket disputes.
- 847 of 1,247 severity labels are automated pre-labels; use the
  human-adjudicated subset for primary evaluation.
- The litigation stream is non-stationary; results on random splits may not
  hold under temporal shift.

## Distribution and maintenance

- **TODO:** hosting location (anonymized for review), file formats, and version.
- **TODO:** maintainer contact (after the review period) and update policy.
- **TODO:** procedure for removal requests concerning names in public filings.
