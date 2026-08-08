# AAAI &rarr; ACL conversion notes

This directory is the **ACL Rolling Review (*ACL)** version of the ALERT paper,
converted from the original AAAI-2027 submission source
(`../alert_aisuit_7p_aaai_20260607_1800.zip`). The scientific content is
unchanged; only the venue formatting and the mandatory structural sections were
adapted.

## What changed

### Template / formatting
- Switched the document class driver to the official ACL style: `main.tex` now
  uses `\documentclass[11pt]{article}` + `\usepackage[review]{acl}` instead of
  the AAAI `aaai2026` style.
- Style files `acl.sty` and `acl_natbib.bst` are the official ACL versions
  (from `github.com/acl-org/acl-style-files`, `master`).
- Removed AAAI-only preamble machinery: `\pdfpagewidth/\pdfpageheight`,
  `\pdfinfo{/TemplateVersion}`, the `\refurl`/`\pdfstartlink` "clickable link
  without hyperref" hack (ACL uses `hyperref`, loaded by `acl.sty`), and the
  manual `\usepackage[switch]{lineno}`/`\linenumbers` (the `review` option of
  `acl.sty` provides line numbers automatically).
- Dropped duplicate `\usepackage{natbib}` and `\usepackage{caption}` — both are
  loaded by `acl.sty`, so reloading them clashes.

### Anonymity
- Title block (`001_title.tex`) no longer says "Under double-blind review for
  AAAI 2027". In `review` mode `acl.sty` prints "Anonymous ACL submission" and
  hides the author block; replace the placeholder authors for the camera-ready
  (`\usepackage{acl}`, i.e. drop the `review` option).

### Required ACL structure
- **`Limitations`** is now a dedicated unnumbered section
  (`086_limitations.tex`), placed after the Conclusion and before the
  References. **This section is mandatory at *ACL venues** and its absence is
  grounds for desk rejection. Its content is drawn entirely from caveats
  already present in the original paper (bounded guarantees, unfinished P1
  transfer, small PLRE benchmark, two-rater RQ2, retained-label circularity,
  U.S./English-only coverage, extractor recall) — nothing was invented.
- **`Ethics Statement`** is now a dedicated unnumbered section
  (`087_ethics.tex`), assembled from the decision-support boundary, human-in-
  the-loop, and data-governance paragraphs of the original Discussion.
- The AAAI "Reproducibility Checklist" file (`089_repro_checklist.tex`) is **not
  included** — ACL/ARR collects the *Responsible NLP Research* checklist through
  the submission portal, not in the PDF. The technical appendix already contains
  the reproducibility material.
- The reference to "AAAI Responsible AI guidance" was reworded to a
  venue-neutral data-governance statement.

### Appendix
- `\appendix` is now issued once, by `main.tex`, immediately after
  `\bibliography` (ACL places appendices *after* the references). The duplicate
  `\appendix` and the stray `[cite: 7]` / non-English comments inside
  `088_appendix.tex` were removed.

## Build

```bash
./gen_pdf.sh          # pdflatex + bibtex + pdflatex x2
```

The PDF could **not** be compiled in the automated environment that produced
this conversion (the TeX package server used by the available toolchain is
blocked by the egress policy). The source was verified statically instead: every
`\cite`/`\nocite` key resolves against `reference-data.bib`, every
`\ref`/`\eqref` resolves to a defined `\label`, there are no duplicate labels,
and no package is double-loaded. **Compile once on Overleaf or a local TeX Live
before submitting.**

## Still to check before submitting (cannot be done by editing alone)

1. **Page length.** ACL long papers allow **8 content pages** (Limitations,
   Ethics, References, and Appendix do not count). The original AAAI body was 7
   pages; confirm the ACL two-column reflow stays within 8.
2. **Run Protocol P1** (external-stack transfer of the validity gate) — the
   original authors' own notes call this the single highest-value,
   accept/reject-determining experiment still outstanding.
3. **De-anonymization.** Ensure `ai-suit-tracker` / `ai-suit-sensing.csv` and
   any released repository link do not reveal authorship during the anonymity
   period.
4. **Responsible NLP Research checklist** — complete it in the submission portal.
