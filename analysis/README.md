# Review statistics

`compute_review_stats.py` computes every number the simulated ACL reviews asked
for, from your own experiment outputs. Export the CSVs below and run one command.
The script writes a readable report (`review_stats.md`) and LaTeX macros
(`review_stats.tex`) that can be pasted into the paper.

```bash
python compute_review_stats.py \
  --rq1 rq1_predictions.csv --plre plre_predictions.csv \
  --annotations severity_annotations.csv --plre-annotations plre_annotations.csv \
  --rq2 rq2_ratings.csv --calls llm_calls.csv --calibration calibration_cases.csv \
  --out-dir out/
```

Any file can be omitted; its section is skipped. Python 3.10+, standard library
only. Install SciPy for exact Wilcoxon p-values; without it the script falls back
to a normal approximation (up to about ±0.03 off at n = 15).

## What each file produces

| File | Review item | Statistics |
|---|---|---|
| `rq1_predictions.csv` | W-A, W3, W-C | test size by label source; whether human cases fall in train/validation (leakage check); macro F1/P/R with 95% CIs and paired-bootstrap p vs. ALERT, on the human-adjudicated and full test sets, for baselines **and ablation variants** |
| `plre_predictions.csv` | W-A, W1, W2, W-F | pair counts, positive rate, distractor share; F1 with CIs and p-values (Tables 4 and 6); the same **without stale-authority distractors**; per-archetype F1 |
| `severity_annotations.csv` | W-E | pairwise Cohen's κ, **Fleiss' κ**, Krippendorff's α for the three annotators |
| `plre_annotations.csv` | W1 | the same agreement statistics for PLRE labels |
| `rq2_ratings.csv` | W5 | Krippendorff's α (interval) between raters; Wilcoxon p-values with **Holm correction** over all comparisons |
| `llm_calls.csv` | W-B | mean and median LLM calls and tokens per case for each system |
| `calibration_cases.csv` | W4 | calibration-set size |

## Input formats

Column order does not matter; extra columns are ignored. Example rows are in
`templates/`.

**rq1_predictions.csv**: one row per (case, system).
`case_id, split (train|validation|test), label_source (human|retained), gold, system, pred`.
`gold` and `pred` are severity labels (`High`, `Medium`, `Low`). Include ablation
variants as extra systems (for example `ALERT-noGoalChecker`). The reference
system is `ALERT` (`--reference-system`).

**plre_predictions.csv**: one row per (pair, system).
`pair_id, case_id, archetype, split, is_distractor (0|1), gold (0|1), system, pred (0|1), stale_cite (0|1, optional)`.
Name the no-gating variant `ALERT-flat` (or pass `--flat-system`).

**severity_annotations.csv** / **plre_annotations.csv**: one row per (item, annotator).
`item_id, annotator, label`.

**rq2_ratings.csv**: one row per (case, system, rater, dimension).
`case_id, system, rater, dimension, score (1–5)`.

**llm_calls.csv**: one row per (case, system).
`case_id, system, calls, prompt_tokens, completion_tokens`.

**calibration_cases.csv**: `case_id` of each conformal calibration case.

## Checking the script

```bash
python make_synthetic.py synthetic/       # random example inputs
python -m unittest test_compute_review_stats.py
```

The tests check every statistic against scikit-learn, statsmodels, krippendorff,
and SciPy when they are installed.
