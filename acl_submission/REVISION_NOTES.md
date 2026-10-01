# ACL submission polish — revision notes

Build: `./gen_pdf.sh` compiles cleanly with TeX Live 2023 (0 undefined refs/citations,
0 overfull boxes, 0 BibTeX warnings). **Body now ends on page 8** (was ~8.3 pages →
over the ACL long-paper limit). Limitations / Ethics / References / Appendix follow.
A compiled `main.pdf` is included for convenience.

## What changed

### Framing (for an ACL/NLP audience)
- **Title** → *ALERT: Point-in-Time Authority Gating for Product–Litigation Risk
  Entailment*. The old title ("Goal-Conditioned Agentic Systems for Self-Verifying
  Risk Intelligence") did not mention the NLP task or the retrieval mechanism.
  Previous titles are kept as comments in `001_title.tex`.
- **Abstract** rewritten around the problem (RAG treats stale precedent as valid
  evidence) → task (PLRE) → method → headline numbers (PLRE F1 0.72→0.78, stale
  citations 12.7%→4.1%, human-subset F1 0.79 vs 0.75). No new claims.
- **Introduction** tightened; repeated defensive phrasing ("not an agent wrapper",
  "not a post-hoc explanation") removed; contributions as a list with section links.

### Structure and page budget
- Background shortened; its Legal-NLP and agentic-RAG paragraphs merged into
  Related Work (they duplicated it).
- Duplicate subsection title fixed: §3.1 "Goal-Conditioned Agentic Loop" (same as
  §4.4) → "Goal Predicate and Stopping Rule".
- The two RQ1 tables (human-only and full test) merged into one body table
  (human-only F1/P/R + full-test F1). The full-test P/R table moved to the appendix,
  where it **replaces an exact duplicate** of the human-only table (old Table A.7).
- Discussion and Conclusion condensed (content overlapped with Limitations).
- Appendix "Retriever Ablation" section renamed "Additional Results and Ablations"
  (it also held schema-completeness and loop ablations).

### Correctness / consistency fixes
- RQ6 & appendix: text said the temporal split exceeds the risk budget; at α=0.20 it
  does not (0.196 < 0.20). Now states it exceeds the target at α=0.05 and 0.10 only.
- Appendix no longer says Table A (robustness) "confirms the ordering is preserved":
  the table has only ALERT rows. See action item 2.
- Coverage loss L_τ defined consistently ("retrievable" High-risk theory) in the main
  text and in the conformal-calibration appendix.
- RQ2 now names the test (Wilcoxon signed-rank, as in the appendix) and the scale.
- Misplaced citation removed (Bommasani et al. was cited for "filings concentrated in
  2023–2025").
- Overfull equations/tables fixed (argmax objective, Eq. 3 split over two lines,
  L_τ displayed, appendix table resized).

### Bibliography
- `xiao2021lawformer`: `@inproceedings` with a journal as booktitle → `@article`.
- `angelopoulos2021ltt`: arXiv preprint as booktitle → `@misc`.
- Added standard ACL-community references reviewers will expect:
  COLIEE (Rabelo et al., 2022), neural LJP (Chalkidis et al., ACL 2019),
  LexGLUE (Chalkidis et al., ACL 2022), time-aware LMs (Dhingra et al., TACL 2022).
  **Please double-check page numbers/venues of these four entries.**

## Action items for the authors (cannot be fixed by editing alone)

1. ~~Edge-sensitivity table (Table 5) ambiguity~~ — **resolved.** Authors confirmed
   the masks are applied *on top of the extractor output*. Rows relabelled
   ("+ mask x% of extracted"), an approximate effective-miss-rate column added
   (1 − 0.77·(1 − x)), caption and RQ3 text rewritten, and the P2 appendix wording
   aligned (23% = extractor's own miss rate, not a masking level). No numbers changed.
2. ~~Backbone robustness~~ — **resolved by softening.** Authors confirmed baselines
   were not run on the Llama-3.1-70B + bge stack. The claim that the baseline ranking is
   preserved was removed from RQ6, Limitations, and the appendix; the text now states only
   what Table (robustness) shows (full system F1 0.81→0.76, 2.4→2.6 iterations), and
   Limitations names backbone-matched baseline comparisons as an open test. If baseline
   runs on the open-weights stack become available, add them to that table.
3. **Protocol P1** — **not executed; claims adjusted.** Authors confirmed there are no
   P1 results. Generality claims now match the evidence: Introduction and Discussion
   say the operator is general in form but evaluated only on U.S. AI litigation
   within ALERT; Limitations states the gains should not be read as evidence for
   other retrievers or domains. "Pre-registered" was changed to "pre-specified"
   throughout (the protocols are not deposited in an external registry; if they
   are, e.g. on OSF, restore the term and add the link after review). Running P1
   remains the single experiment most likely to strengthen the paper.
4. ~~Responsible NLP checklist~~ — **drafted.** Ethics Statement now states the
   dataset/code licenses (CC BY 4.0 / MIT), source-data terms and personal names in
   public filings, annotator recruitment/payment (institution staff, regular duties),
   verbal consent, why no ethics-board review was sought, and AI-assistant use
   (editing only). Draft form answers with section references are in
   `RESPONSIBLE_NLP_CHECKLIST.md`. C1/C4/D5 answered: App. G now has a *Models,
   compute, and software* paragraph (models named; GPU hours and API cost were not
   logged; package versions pinned in the released code's dependency file); D5 is
   answered "No" (demographics not collected). **Ship a pinned dependency file with
   the released code:** a draft `requirements.txt` and a pinning script are in
   `code_release/` (see its README); run the script in the experiment environment
   and ship the generated `requirements.lock.txt`.
5. ~~Anonymity~~ — **resolved in the paper.** Distinctive identifiers replaced for
   review via two macros in `main.tex`:
   `\trackername` = `alert-tracker` (was `ai-suit-tracker`) and
   `\schemafile` = `alert-sensing.csv` (was `ai-suit-sensing.csv`).
   Appendix no longer lists source-file paths (`src/*.py`), the `v02` version tag,
   the `aisuit` issue label, or exact environment-variable names (these are
   matchable by GitHub code search); the configuration table uses descriptive
   parameter names instead. An author-facing note about identifiers was removed
   from the Ethics Statement. PDF and figure metadata were checked (no author info).
   **Camera-ready:** restore the two macros and the original appendix identifiers.
   **Still on you:** (a) the anonymous code/data link in the supplement must be an
   anonymized mirror (e.g. anonymous.4open.science), not this repository or the
   tracker repository; (b) the released artifact should use the anonymized names
   or be withheld until after review; (c) this repository (`alert-aisuit`) contains
   the AAAI zip/PDF — keep it private or out of any link given to reviewers.
6. Verify all numbers once more against your logs — no numbers were changed, only
   re-presented.

## Reviewer-simulation follow-ups (W7, W9)

- **W9 (systems vs. NLP balance):** architecture figure, discovery/schema-population
  subsection, and the annual ingestion table moved to the appendix (App. D.1 and
  App. A); §4.1 now frames the sensing pipeline as infrastructure and points to the
  NLP components; RQ4 shortened to one sentence. Freed space holds a schematic PLRE
  instance table (Table 1, explicitly illustrative, built from examples already in
  the paper) and the new related-work paragraph.
- **W7 (related work):** new *Time-sensitive QA and temporal retrieval* paragraph
  (SituatedQA, TimeQA, StreamingQA, RealTime QA, CronKGQA, temporal IR survey) that
  distinguishes time-stamped facts from supersession; *Citators and legal citation
  graphs* now cites citation-network analysis (Fowler et al., 2007) and automatic
  citation-edge labeling (Sadeghian et al., 2018), and states plainly that the
  scoring function is simple and the contribution is the validated treatment layer.
  **Please verify the bibliographic details of these eight new entries.**
- **W6 (operator is simple / w(·) unspecified):** contribution reframed from "a
  retrieval mechanism" to "an extracted, citator-validated treatment layer";
  §4.5 adds a *Why not a date filter?* paragraph (the end of a validity interval is
  set by later documents and must be inferred from treatment edges, so a date
  filter cannot express it); Discussion and Conclusion aligned. To stay within 8
  pages, duplicated passages were removed (Discussion "Error propagation",
  Background "Why time matters" / "Decision-support boundary"; the same content
  remains in §4.5, RQ3, Introduction, Related Work and Ethics).
  **Still open:** the exact w(·) values — send them and they will be stated under Eq. 3.
- **W1 (PLRE under-specified):** no additional numbers are available, so reporting is
  made explicit instead. RQ5 states that PLRE scale is case-level only and that
  pair-level composition and a PLRE-specific κ are not reported (the κ in §5 is for
  severity labels); RQ3 and the Table 4 caption say only the full-vs-flat gap was
  significance-tested and the 3-point intermediate step is directional; Table 6 is
  labeled as point estimates; Limitations lists the missing statistics.
  **If you can compute them later** (pair count, positive rate, distractor share,
  test size, PLRE κ, bootstrap CIs for Tables 4/6), adding them would remove this
  weakness rather than just disclosing it.
- **W4 (Proposition 1 mostly definitional):** text now says the termination clause
  follows almost directly from the definitions and that attainable progress (A2) is
  an unverified design assumption (appendix no longer claims the mean iteration
  count "validates" it); the conformal clause is named as a standard application,
  limited to exchangeable cases and violated by the temporal split at α ∈ {0.05,
  0.10}; "retrievable" is defined (supported by ≥1 authority valid at t_q in D);
  calibration-set size is disclosed as unreported. **If you know n, add it.**
- **W5 (RQ2 weak):** RQ2 now states the comparison is paired by case (same 15 cases
  per system), that p-values are uncorrected for 20 comparisons, and that
  inter-rater agreement was not computed; appendix and Limitations aligned.
  Typo "Clarity. on a 5-point scale" fixed.
- To keep 8 pages: case study / live-monitoring subsection moved to App. D; the
  Conclusion's open-problems sentence now points to Limitations; Discussion
  "Construct validity" tightened.
- **W10 (dataset construction):** new App. A.1 *Inclusion Criteria and Case Unit*
  (retrospective RECAP keyword search over AI-training × legal-theory × data-source
  term families, manual screening for AI development/training/deployment at issue,
  litigation type assigned afterwards from the cause of action, one case = one
  docket with consolidated actions not merged); one-sentence summary in §5.1;
  Limitations notes per-docket counting over-represents multi-docket disputes.
  Keyword families are described generically (exact query strings would match the
  public tracker repository and break anonymity).
- **W11 (reproducibility):** App. G *Code and data release* commits to releasing all
  code (tracker, treatment-edge extraction and graph construction, PLRE evaluation,
  agentic loop) plus w(·), prompts with few-shot examples, splits, seeds and the
  dataset; an anonymized copy is supplementary material for review. §5.2 and App. D
  aligned. **You must actually include the anonymized code and data in the
  supplement**, and send the few-shot prompt text if you want it in the appendix.
- To keep 8 pages: Conclusion rewritten more compactly; duplicated sentences removed
  from Discussion and RQ6.
- **W2 (labels favour gating by construction):** no distractor-free numbers exist, so
  RQ5 and Limitations now say that PLRE labels encode temporal validity, that no
  distractor-free comparison is reported, and that part of the gating gain may come
  from rejecting stale distractors. **If computed later, report gated vs. flat F1 on
  the subset without stale-authority distractors.**
- **W3 (RQ1 setup):** B2–B5 use the same GPT-4o backbone and decoding settings as
  ALERT; B5 is matched on iterations, not tokens; the training split is used only for
  few-shot selection and threshold tuning (no LLM fine-tuning); adjudicators did not
  see the pre-labeler's score; the 91% spot-check is flagged as lenient; the
  human-adjudicated test size is disclosed as unreported (≈80 if spread evenly).
  **If you know the exact test n, add it.**
- To keep 8 pages: RQ4 moved to the appendix (still defined in §6.1); RQ3's
  critique-loop explanation shortened to a pointer to §4.5.
