# Responsible NLP Research checklist — draft answers

Draft answers for the ARR submission form. Section numbers refer to the current
`main.pdf`. The form's exact wording changes between cycles, so match each answer
to the question IDs on the live form. Items marked **TODO** need facts that are
not in the paper.

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
| B1. Cited the creators of artifacts used? | **Yes** | §4.2–4.3 (CourtListener, LegalBERT, DPR); §6 (baselines); references. |
| B2. License / terms of use discussed? | **Yes** | *Ethics Statement*: dataset CC BY 4.0, code MIT; source data used under CourtListener/RECAP terms; citator outputs used only as an evaluation reference under a licensed account (App. I.2). |
| B3. Use consistent with intended use? | **Yes** | *Ethics Statement*: research on legal-risk analysis, decision support only; not for automated legal decisions. |
| B4. Personally identifying info / offensive content? | **Yes** | *Ethics Statement*: records contain party and counsel names as they appear in public court filings; no other personal information is collected. |
| B5. Documentation of artifacts (domain, language, coverage)? | **Yes** | §5 (coverage 2020–2025, litigation types, defendants); *Limitations* (U.S. federal, English only); App. A (schema). |
| B6. Statistics (splits, sizes)? | **Yes** | §5 (Tables 1–2), §6.1 (70/10/20 split; 400 human-adjudicated, 847 retained pre-labels), §6.6 (312 PLRE cases). |

## C. Computational experiments

| Item | Answer | Where / justification |
|---|---|---|
| C1. Model size, compute budget, infrastructure? | **Partially — TODO** | Models are named (GPT-4o via API, Llama-3.1-70B, App. G/H). **Missing:** GPU type and hours for Llama-3.1-70B and the LegalBERT fine-tuning; API cost or number of calls for GPT-4o. Add a sentence to App. G or answer on the form. |
| C2. Experimental setup and hyperparameters? | **Yes** | App. G (hyperparameter table: *k*, τ, T_max, temperature, thresholds; prompt schematic; split protocol). |
| C3. Descriptive statistics (error bars, number of runs)? | **Yes** | §6.2 (paired-bootstrap intervals, 10,000 resamples); App. G (5 seeds); App. H (mean ± std over runs). |
| C4. Existing packages and their settings? | **Partially — TODO** | Models and APIs are named, but software libraries are not (BM25 implementation, re-ranker, conformal/bootstrap code). List them in App. D/G or answer on the form. |

## D. Human annotators / participants

Three legal research specialists adjudicated labels (§5.2); two specialists rated reports (§6.3).

| Item | Answer | Where / justification |
|---|---|---|
| D1. Full annotation instructions? | **Yes** | Guidelines released with the dataset (§5.2, *Ethics Statement*). They are not reproduced in the PDF; say so on the form. |
| D2. Recruitment and payment? | **Yes** | *Ethics Statement*: institution staff, work done within regular paid duties, no additional compensation. |
| D3. Consent and how data would be used? | **Yes** | *Ethics Statement*: participants were told how their annotations would be used and agreed verbally. |
| D4. Ethics review board approval? | **No** | *Ethics Statement*: not sought, because the work labeled public court documents and collected no personal information about participants. |
| D5. Annotator demographics? | **No — TODO (optional)** | Only professional background is reported ("legal research specialists"). If available, add jurisdiction of legal training and years of experience. |

## E. AI assistants

| Item | Answer | Where / justification |
|---|---|---|
| E1. Use of AI assistants reported? | **Yes** | *Ethics Statement*: used only to edit and polish the text; ideas, design, experiments and analyses are the authors'. |

## Remaining TODOs before submitting

1. **C1**: GPU type and hours (Llama-3.1-70B runs, LegalBERT fine-tuning) and GPT-4o usage (number of calls or cost).
2. **C4**: software libraries and versions (BM25, re-ranker, bootstrap/conformal code).
3. **D5** (optional): annotator background details.
4. Confirm that the released guideline file and the dataset card state CC BY 4.0, and the code repository states MIT.
