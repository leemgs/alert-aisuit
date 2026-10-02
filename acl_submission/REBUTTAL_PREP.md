# Author-response preparation

Draft answers to the criticisms raised in the two simulated reviews, for the ARR
author-response period. Each answer uses only facts already in the paper.
Placeholders in `[brackets]` come from `analysis/review_stats.md` once the
script has been run on the real outputs. **Never fill a placeholder by hand.**

ARR responses are short; pick the 3–5 points the actual reviewers raise and
answer them in this order: concede what is true, give the number, point to where
it will appear in the revision.

---

## 1. "PLRE is small and under-specified" (W1 / W-A)

> We agree the PLRE benchmark is initial (312 cases, five archetypes; §6.5,
> Limitations). It contains [plreNPairs] attribute–theory–date pairs, of which
> [plreTestPairs] are in the test split; the positive rate is [plrePosRate]% and
> stale-authority distractors make up [plreDistractorShare]%. With 95% bootstrap
> intervals, full gating reaches [plreFAllFull] F1 [plreCIAllFull] vs.
> [plreFAllFlat] [plreCIAllFlat] for flat similarity. We will add these to §6.5
> and Table 6.

## 2. "Labels reward the gate by construction" (W2)

> PLRE labels deliberately encode temporal validity, which is the property the
> task is meant to test (§4.5); validity is judged by annotators reading opinion
> text, independently of our extracted graph. To separate this from distractor
> rejection, on pairs *without* stale-authority distractors the gate scores
> [plreFNoDistrFull] [plreCINoDistrFull] vs. [plreFNoDistrFlat]
> [plreCINoDistrFlat]. [Interpret honestly: if the gap shrinks, say most of the
> gain comes from rejecting stale support, which is the intended behavior.]

## 3. "RQ1 test size and leakage" (W3)

> **Answer only after confirming the facts.** If the 400 human-adjudicated cases
> include training/validation cases used for few-shot examples or thresholds,
> report RQ1 on the human-adjudicated *test* cases only ([rqOneHumanTestN] cases)
> and say so plainly. B2–B5 share ALERT's GPT-4o backbone and decoding settings
> (§6.1).

## 4. "B5 is not compute-matched" (W-B)

> B5 is matched on refinement iterations, not on LLM calls; we renamed it
> accordingly. Per case, ALERT uses [callsALERT] calls and [tokensALERT] tokens on
> average vs. [callsBFive] and [tokensBFive] for B5. [If ALERT uses clearly more
> compute, say so and state that the gate result (Table 4) does not depend on
> the agent loop.]

## 5. "Agent-loop ablation uses the full test set" (W-C)

> On the human-adjudicated subset, removing the Goal Checker changes macro F1
> from [..] to [..] (paired bootstrap p = [..]). We will report Table A.8 on that
> subset.

## 6. "The gate is just a date filter" (W6)

> Once intervals are known the gate is intentionally simple (§4.4, "Why not a
> date filter?"). The contribution is inferring the interval ends: an
> authority's end date is set by *later* opinions, so it must be extracted from
> treatment edges and validated. We do this against 600 gold spans (negative-
> treatment P/R 0.84/0.77) and a commercial citator (micro-F1 0.81, 20.4% missed
> closures, 3.8% PLRE decision flips; App. I.2).

## 7. "Generality is untested" (W8, P1)

> We agree and say so in Limitations. The transfer protocol (P1) is fully
> specified in App. I.1, including acceptance criteria fixed in advance.
> [If P1 has been run by the response period, report its pre-specified
> endpoints exactly as defined there, including a failure on slice (b).]

## 8. "Inter-annotator agreement with three annotators" (W-E)

> The κ = 0.74 in §5.2 is [state which statistic it is]. Fleiss' κ over all three
> annotators is [sevFleissKappa] (Krippendorff's α [sevKrippAlpha]).

## 9. "RQ2 is weak" (W5)

> We agree RQ2 is supporting evidence only (two raters, 15 cases). Krippendorff's
> α between raters is [rqTwoAlpha]; after Holm correction over all 20 comparisons,
> [rqTwoHolmSig] remain significant.

## 10. "Calibration-set size" (W4)

> Conformal calibration uses [calibN] cases. The guarantee holds for exchangeable
> cases only; the temporal split exceeds the target at α = 0.05 and 0.10
> (Table A.11), which is why we recommend rolling re-calibration.

## 11. "Is the dataset/code available?" (W11)

> An anonymized copy of the code and data is in the supplementary material
> (App. G); the public release follows the review period under CC BY 4.0 / MIT.
> [Only say this if the supplement actually contains the code that produced the
> results.]
