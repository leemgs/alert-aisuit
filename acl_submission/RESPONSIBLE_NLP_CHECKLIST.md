# Responsible NLP Research checklist — draft answers

Draft answers for the ARR submission form. Section numbers refer to the current
`main.pdf`. The form's exact wording changes between cycles, so match each answer
to the question IDs on the live form.

Answer to "Did you ...?" questions with **Yes / No / N/A** plus a section reference
and, where useful, a one-line justification.

## A. For every submission

| Item | Answer | Where / justification |
|---|---|---|
| A1. Limitations discussed? | **Yes** | *Limitations* section (after §9). |
| A2. Potential risks discussed? | **Yes** | *Ethics Statement*: decision-support boundary (not legal advice), human oversight of failure modes, data governance; *Limitations*: extractor recall, temporal shift. |

## B. Scientific artifacts

Uses artifacts: CourtListener/RECAP data, LegalBERT, GPT-4o, `text-embedding-3-large`, Gemini embeddings, Llama-3.1-70B, `bge-large`. Creates artifacts: ALERT-Dataset, annotation guidelines, code, evaluation scripts.

| Item | Answer | Where / justification |
|---|---|---|
| B1. Cited the creators of artifacts used? | **Yes** | §4.1–4.2 (CourtListener, LegalBERT, DPR); §6.1 (baselines); App. D.1; references. |
| B2. License / terms of use discussed? | **Yes** | *Ethics Statement*: dataset CC BY 4.0, code MIT; source data used under CourtListener/RECAP terms; citator outputs used only as an evaluation reference under a licensed account (App. I.2). |
| B3. Use consistent with intended use? | **Yes** | *Ethics Statement*: research on legal-risk analysis, decision support only; not for automated legal decisions. |
| B4. Personally identifying info / offensive content? | **Yes** | *Ethics Statement*: records contain party and counsel names as they appear in public court filings; no other personal information is collected. |
| B5. Documentation of artifacts (domain, language, coverage)? | **Yes** | §5.1 and App. A.1 (coverage 2020–2025, inclusion criteria, case unit, defendants); *Limitations* (U.S. federal, English only, per-docket counting); App. A (schema, Table A.2). |
| B6. Statistics (splits, sizes)? | **Yes** | §5.1 (Table 2), App. A (Table A.2), §6.1 (70/10/20 split; 400 human-adjudicated, 847 retained pre-labels), §6.5 (312 PLRE cases). |

## C. Computational experiments

| Item | Answer | Where / justification |
|---|---|---|
| C1. Model size, compute budget, infrastructure? | **Partially** | App. G, *Models, compute, and software*: models and sizes named (GPT-4o via API; Llama-3.1-70B, 70B parameters; LegalBERT; embedding models). GPU hours and API cost were **not logged**; scale is indicated by mean 2.4 loop iterations per case (T_max = 5) and five test-set evaluation runs. Suggested form text: "We did not track GPU hours or API cost; App. G reports the models used and the per-case loop budget." |
| C2. Experimental setup and hyperparameters? | **Yes** | App. G (hyperparameter table: *k*, τ, T_max, temperature, thresholds; prompt schematic; split protocol). |
| C3. Descriptive statistics (error bars, number of runs)? | **Yes** | §6.2 (paired-bootstrap intervals, 10,000 resamples); App. G (5 seeds); App. H (mean ± std over runs). |
| C4. Existing packages and their settings? | **Yes** | App. G, *Models, compute, and software*: exact packages and versions are pinned in the dependency file of the released code; model settings in App. G (hyperparameter table). **Make sure the released code includes that dependency file.** |

## D. Human annotators / participants

Three legal research specialists adjudicated labels (§5.2); two specialists rated reports (§6.3).

| Item | Answer | Where / justification |
|---|---|---|
| D1. Full annotation instructions? | **Yes** | Guidelines released with the dataset (§5.2, *Ethics Statement*). They are not reproduced in the PDF; say so on the form. |
| D2. Recruitment and payment? | **Yes** | *Ethics Statement*: institution staff, work done within regular paid duties, no additional compensation. |
| D3. Consent and how data would be used? | **Yes** | *Ethics Statement*: participants were told how their annotations would be used and agreed verbally. |
| D4. Ethics review board approval? | **No** | *Ethics Statement*: not sought, because the work labeled public court documents and collected no personal information about participants. |
| D5. Annotator demographics? | **No** | Only professional background is reported (legal research specialists, institution staff). Demographic data were not collected; with 3 annotators and 2 raters, detailed characteristics could also compromise anonymity. |

## E. AI assistants

| Item | Answer | Where / justification |
|---|---|---|
| E1. Use of AI assistants reported? | **Yes** | *Ethics Statement*: used to edit and polish the text, and an AI coding assistant wrote the P1 pilot code (App. I.1) to a design frozen by the authors before any run; ideas, system design and the other experiments and analyses are the authors'. **If any reported statistic is computed with `analysis/compute_review_stats.py` (written with an AI assistant), extend the statement**, e.g.: "AI assistants also helped write statistical-analysis scripts, which we verified against standard libraries." |

## Before submitting

All items have draft answers. Remaining actions:

1. The released code must include a pinned dependency file, since C4 points to it. Run `code_release/pin_requirements.py` in the experiment environment and ship the generated `requirements.lock.txt` (see `code_release/README.md`).
2. Confirm that the dataset card states CC BY 4.0 and the code repository states MIT (B2).
3. Copy the answers into the ARR form and check the item IDs against the current form.
