# Final pre-submission check (ARR / ACL 2027, long paper)

Build: `./gen_pdf.sh` (review mode) → `main.pdf`, 20 pages.

## 1. Desk-reject checks (verified on the current build)

| Check | Status | Evidence |
|---|---|---|
| Official style file | OK | `acl.sty` is identical to `acl-org/acl-style-files` master |
| Review mode (anonymous, line numbers) | OK | "Anonymous ACL submission", line numbers on every page |
| Page limit (8 pages for long papers) | OK | Conclusion ends on p. 8; Limitations starts on p. 9 |
| Limitations section (required) | OK | unnumbered, after Conclusion, before References |
| No layout hacks | OK | no `\vspace` in the body, no changes to margins, line spacing or caption spacing |
| Fonts | OK | all 27 fonts embedded, no Type 3 |
| LaTeX/BibTeX | OK | 0 undefined references, 0 BibTeX warnings |
| Placeholders | OK | no TODO, `??`, `[sev…]` or `[rq…]` placeholders in the `.tex` files |
| Anonymity in paper | OK | no names, repository URLs or affiliations; PDF title/author metadata empty; `\trackername` / `\schemafile` are anonymized |
| Anonymity in supplement | **Author action** | build it with `supplement/anonymize_supplement.py` (now also replaces the "By Gauss" column label); it refuses to zip if anything identifying remains |

## 2. Reviewer-style assessment of the current version

**Summary.** The paper introduces PLRE (does an AI product's attributes entail
exposure to a legal-risk theory under authority valid at a query date?) and
ALERT. ALERT's core is a treatment layer extracted from later opinions that
closes validity intervals, applied as a retrieval-time gate. The paper also
contributes a goal-conditioned agent loop with conformal control of evidence
omission, and a 1,247-case dataset.

**Strengths.**
- Clear, well-motivated problem (stale but similar precedent in RAG). The paper
  explains why the gate is not just a date filter: the interval end is set by
  later documents.
- The treatment layer is validated against gold spans *and* a commercial citator
  (P2, micro-F1 0.81). Edge-error propagation is audited (Table 5).
- Claims are carefully scoped: primary results use only the human-adjudicated
  subset, circularity is acknowledged, and a negative transfer pilot (P1) is
  reported honestly.
- Strong ethics, licensing and data-governance statements.

**Weaknesses a reviewer is likely to raise.**
1. **Statistics the paper says it does not report.** The text lists these as
   missing: calibration-set size, test-split size of the human-adjudicated subset,
   PLRE pair counts, positive rate and distractor share, PLRE inter-annotator
   agreement, and RQ2 inter-rater agreement. Each "we do not report X" invites
   "why not?". These are the cheapest points to win back.
2. **PLRE significance.** Tables 4 and 6 have no confidence intervals beyond the
   full-vs-flat test, and the benchmark partly rewards what the gate enforces
   (stale distractors). A distractor-free subset result would answer this
   directly.
3. **The central equation is under-specified.** The values of `w(·)` are not
   given in the paper (App. G promises them in the code).
4. **Generality.** The P1 pilot met its pre-fixed criterion on 1 of 3 hosts. This
   is honest, but it narrows the contribution to "within ALERT".
5. **κ with three annotators** is described as Cohen's κ, which is defined for
   two raters. State whether it is mean pairwise Cohen's κ, or report Fleiss' κ.
6. Baselines were not re-run on the open-weights backbone, and RQ2 is small
   (15 cases, 2 raters).

**Likely scores as is:** Soundness 3/5, Overall around 3 (Findings-level). If you
close items 1–3 and 5 with real numbers, Soundness 3.5–4 is realistic.

## 3. Author-supplied values (status)

The authors supplied the values below on 2026-10-05 and confirmed that all of them
were measured on the actual data. They are now in the paper.

| # | Item | Value in the paper | Where |
|---|---|---|---|
| A | `w(·)` schedule | 1.00 positive/open, 0.75 cautionary, 0.50 material narrows; overruled/superseded removed by the indicator | §4.4, Table A.10 |
| B | Human-adjudicated test split; calibration set | 82 cases; 150 cases | §3.1, §6.1, Limitations |
| C | Severity-label agreement | Cohen's κ 0.74; Fleiss' κ 0.72 (3 annotators) | §5.2 |
| D | RQ2 inter-rater agreement | mean Cohen's κ 0.68 (0.62–0.74 by scale) | §6.3, App. G |
| E | PLRE composition; full-vs-flat CI | 1,856 pairs, 28.4% positive, 19.7% stale distractors, PLRE κ 0.71; ΔF1 95% CI [3, 9] points | §6.4, §6.5, Table 4, Limitations |
| F | 0.81 F1 is on the full held-out test set | confirmed by the authors | §6.4, §6.6 |

**Method change that follows from A.** The paper previously said that material
NARROWS *closes* the validity interval, which would make its weight 0.50 never
apply. The text now says that only OVERRULES/SUPERSEDES close the interval, and
that material NARROWS sets w = 0.50 from its date (§4.4 and the appendix edge-extraction and P2 sections).
**Authors: confirm that this matches the implementation and the Table 4/5 runs.**

### Still open

| # | Item |
|---|---|
| G | Dataset counts. The public dashboard CSV has 562 cases, 314 of them dated 2026, while the paper's dataset covers 2020–2025 (1,247 cases). So the CSV is not a subset of the paper's dataset. The paper does not claim that it is, and should not. Make sure the anonymized supplement contains the 1,247-case release the paper describes. |
| H | Re-run `experiments/p1_pilot/evaluate.py` and `sensitivity.py` (AI-written code) and check Table A.13. |
| I | Still not reported: CIs for Table 6 and for the intermediate step of Table 4, a distractor-free PLRE comparison, Holm-corrected RQ2 tests, and the κ variant behind 0.74 (pairwise mean or a specific pair). These remain stated as limitations. |

## 4. Submission-form items (OpenReview / ARR)

- Responsible NLP checklist: answers drafted in `RESPONSIBLE_NLP_CHECKLIST.md`.
  E1 now discloses the AI-written pilot code.
- Every author needs a complete OpenReview profile. Check the current ARR call
  for its author-reviewing requirement (qualified authors are expected to review).
- Upload the anonymized supplement zip (code and data) built in §1. Keep the
  original GitHub repositories private during review, because exact strings can be
  matched by search.
- Paper type: long. Do not add an acknowledgments section in the review version.
- Before uploading, revoke the GitHub token that appears in plain text in your
  assistant preferences.

## 5. Round-4 review findings (2026-10-06)

Fixed: in App. H, the conformal threshold now uses `sup` instead of `inf` (the
omission risk is non-decreasing in τ, so `inf` would pick the trivial smallest
threshold). The LTT joint (k, τ) guarantee is now stated as high-probability
rather than expected-risk.

Author checks; numbers are not changed here:

| # | Finding | Why a reviewer will notice |
|---|---|---|
| J | Table 3 reports ± 0.02–0.04 on 82 human-adjudicated test cases | a 95% bootstrap CI for macro F1 near 0.79 with n = 82 is usually about ±0.08–0.09. ±0.02 would fit n ≈ 1,500. App. G also says the 5 seeds subsample the test fold, so state what ± measures (CI of F1, CI of the difference vs. B5, or seed spread) and recompute it with `analysis/compute_review_stats.py` |
| K | Calibration set of 150 cases | the loss uses human-labeled High-risk theories, but only 400 cases are human-adjudicated (82 in test). State which split the 150 come from and that they do not overlap the test cases |
| L | Table 5 and P2 still describe NARROWS as a "closure" | after the w(·) change, material NARROWS down-weights rather than closes, while the 0.77 recall and the 20.4% missed-closure rate are micro-averages that include NARROWS. Either re-run on OVERRULES/SUPERSEDES only, or state that "closure" there includes down-weighting edges |
| M | PLRE evaluation split | state whether Tables 4 and 6 use all 1,856 pairs or only test pairs |

### Round-4 follow-up (2026-10-06)

- **J (Table 3 CI):** the authors could not recompute it (no prediction CSV in
  the repository), and a synthetic n = 82 run of `analysis/compute_review_stats.py`
  gave about ±0.09–0.10. The ± columns were therefore **removed** from Table 3
  and Table A.6 (A.6 had the same problem at n ≈ 249). Both tables now report
  point estimates, and the caption and Limitations say so. Once the real
  predictions are available, run the script and add back the F1 CIs and the
  paired ΔF1 CI vs. B5 with its p-value.
- **K (calibration):** stated as 150 cases from the human-adjudicated
  training/validation pool, disjoint from the 82 test cases (author statement).
- **L (NARROWS):** the wording changed instead of re-running. Table 5, P2, the
  Discussion, Limitations and Ethics now speak of negative-treatment *actions*
  (closure for OVERRULES/SUPERSEDES, down-weighting for material NARROWS). The
  numbers are unchanged.
- **M (PLRE split):** stated that Tables 4 and 6 are computed over all 1,856
  pairs. Limitations notes that this includes the pairs used to set the
  validation threshold. A reviewer may ask for held-out test-pair results.
- To keep the body within 8 pages, some sentences in the Introduction, Background,
  §4.5, §6.4, §6.6, Related Work and Conclusion were shortened without dropping
  any claim.
