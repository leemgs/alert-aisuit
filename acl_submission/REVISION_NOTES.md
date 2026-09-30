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

1. **Edge-sensitivity table (Table 5) is internally ambiguous.** The extractor output
   (which itself misses ~23% of closures, 0.77 recall) scores PLRE F1 0.78, while
   "Mask 23% closures" scores 0.74. Reviewers will ask why the same miss rate gives
   different results. Clarify whether masks are applied to *gold* closures or on top
   of the extractor (the row "Mask 10% *additional*" suggests the latter), and, if
   applicable, explain the gap (e.g., extractor misses concentrate on low-confidence
   edges routed to human review).
2. **Backbone robustness.** The text claims the baseline ranking is preserved with
   Llama-3.1-70B + bge, but Table A (robustness) shows only ALERT. Add at least B3/B5
   under the open-weights stack, or soften the claim.
3. **Protocol P1** (external-stack transfer) is still unexecuted; it remains the most
   likely reviewer objection to the "generality" claim.
4. **Responsible NLP checklist** (portal): you will need annotator/rater recruitment,
   compensation, and consent information for the three legal specialists and two
   raters, the license of the released dataset, and any AI-assistant use in writing.
   None of this is stated in the paper; consider one sentence in the Ethics Statement.
5. **Anonymity:** `ai-suit-tracker`, `ai-suit-sensing.csv`, and the GitHub-Actions
   configuration details in the appendix may be searchable and reveal authorship.
   Consider renaming them for the review period.
6. Verify all numbers once more against your logs — no numbers were changed, only
   re-presented.
