# Anonymized supplementary material

`anonymize_supplement.py` builds the anonymized code/data bundle that the paper
promises reviewers (App. G, *Code and data release*).

```bash
python supplement/anonymize_supplement.py \
  --src <path-to-the-code-you-actually-used>:tracker \
  --src <path-to-graph/PLRE/agent-code>:alert \
  --src <path-to-dataset-release>:data \
  --src analysis:analysis --src code_release:code_release \
  --out build/supplement --zip
```

What it does:
- copies each source into `build/supplement/<NAME>/`;
- replaces known identifiers (`ai-suit-*`, `aisuit`, `leemgs`, `aigovsensing`,
  `alert-aisuit`, and the `By Gauss` column label) with the anonymized names the paper uses (`alert-tracker`,
  `alert-sensing`, and so on); add more with `--replace OLD=NEW`;
- drops `.git`, caches, real `.env` files, and images and PDFs (screenshots often
  show account names; use `--keep-images` / `--keep-pdfs` after checking them);
- scans the result for remaining identifiers, e-mail addresses, and personal GitHub
  URLs, and **refuses to write the zip until the scan passes**;
- writes `build/supplement_ANONYMIZATION_REPORT.md` **outside** the bundle,
  because the report names the original identifiers.

Tested on the v02 tracker plus `analysis/` and `code_release/`: 39 files copied,
0 residual findings, and the zip contains none of the original identifiers. A
negative test with an injected e-mail address and GitHub URL fails as intended.

**Important:** the v02 tracker is *not* the version the paper describes (it has no
Gemini deduplication or trend modules). Run the tool on the code that produced the
paper's results. Exact query strings in the code can still be matched against a
public repository by search, so keep the original repositories private during review.

## Dataset card

`DATASET_CARD.md` documents ALERT-Dataset using only facts stated in the paper;
fill in its TODO items, then copy it into the dataset folder you pass with
`--src` so it ships inside the anonymized bundle. (Do not pass this `supplement/`
folder itself: this README names the original identifiers, and the scan will
correctly refuse to build.)
