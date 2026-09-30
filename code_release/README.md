# Code-release dependencies

Files for the dependency list that the paper (Appendix G) and the Responsible
NLP checklist (item C4) refer to.

| File | Status |
|---|---|
| `requirements.txt` | Draft. Section 1 (sensing pipeline) is pinned from the tracker's existing requirements file. Sections 2–4 (LLM APIs, retrieval, evaluation) are inferred from the paper and use `>=` placeholders, **not** the versions used in the experiments. |
| `pin_requirements.py` | Turns the draft into exact versions from a real environment and checks it against the code's imports. Python ≥ 3.10, standard library only. |

## Before release

1. Activate the environment that produced the paper's results.
2. Run:
   ```bash
   python pin_requirements.py --code-dir <path-to-experiment-code>
   ```
3. Fix what it reports, then re-run until it exits with status 0:
   - *listed but not installed*: the package was not used, so delete its line from `requirements.txt`;
   - *imported but not in requirements.txt*: add the package to `requirements.txt`.
4. Ship the generated `requirements.lock.txt` with the anonymized code release.

## Why it is not pinned yet

The code behind the paper's experiments (temporal precedent graph, PLRE evaluation,
agentic loop) is not in this repository. The v02 tracker repository contains only
the sensing pipeline, which has no Gemini, BM25, re-ranker, bootstrap, or conformal
code, so the versions used for those parts cannot be recovered from here.

## Anonymity

Copy only `requirements.lock.txt` (and, if useful, `pin_requirements.py`) into the
anonymized release. Do not link this repository or the tracker repository in the
submission.
