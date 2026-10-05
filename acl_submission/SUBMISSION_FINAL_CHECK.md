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

## 3. Items only the authors can supply (do not submit with invented values)

| # | Item | Where it goes | Tool |
|---|---|---|---|
| A | `w(·)` values (narrowed / cautionary weights) | Table A.10 (`tab:hyperparams`) | — |
| B | Size of the human-adjudicated test split; calibration-set size | §6.1, Limitations, App. H | — |
| C | Which κ is 0.74 (pairwise Cohen's or Fleiss'); Fleiss' κ / Krippendorff's α | §5.2 | `analysis/compute_review_stats.py` |
| D | RQ2 inter-rater α and Holm-corrected p over 20 comparisons | §6.3 | `analysis/compute_review_stats.py` |
| E | PLRE pair counts, positive rate, distractor share; CIs for Tables 4 and 6 | §6.5, Tables 4 and 6 | `analysis/compute_review_stats.py` |
| F | Confirm that Table A.8 and A.12 F1 (0.81) is on the full held-out test set | §6.4 and §6.6 now say "full-test-set" | — |
| G | Dataset counts: the public dashboard CSV has 562 cases with a different yearly distribution from Table A.2 (1,247 cases) | Make sure the anonymized supplement contains the 1,247-case release the paper describes | — |
| H | Re-run `experiments/p1_pilot/evaluate.py` and `sensitivity.py` (AI-written code) | App. I.1 | see `experiments/p1_pilot/README.md` |

After filling any number in, remove the matching "we do not report …" clause in
§3.1, §6.5 and Limitations, and rebuild. Keep the body within 8 pages.

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
