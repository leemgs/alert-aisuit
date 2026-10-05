#!/usr/bin/env python3
"""Build an anonymized copy of code/data for double-blind supplementary material.

    python anonymize_supplement.py --src ../path/to/tracker:tracker \
        --src ../analysis:analysis --out build/supplement --zip

For each --src DIR[:NAME], files are copied into OUT/NAME with:
  * identifying strings replaced (built-in list plus --replace OLD=NEW),
  * identifying file and directory names renamed the same way,
  * excluded paths dropped (.git, caches, real .env files, images and PDFs
    unless --keep-images / --keep-pdfs, plus any --exclude glob).

Afterwards the whole output tree is scanned for anything that still looks
identifying (the replaced strings, e-mail addresses, personal GitHub URLs,
plus --forbid terms). The script writes OUT_ANONYMIZATION_REPORT.md next to
(not inside) the output and exits
with status 1 if anything remains, so the zip is only trusted once it passes.
Only the Python standard library is used.
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import shutil
import sys
import zipfile
from pathlib import Path

# Identifiers known from this project. Longest first so prefixes do not win.
DEFAULT_REPLACEMENTS = [
    ("ai-suit-tracker", "alert-tracker"),
    ("ai-suit-sensing", "alert-sensing"),
    ("ai-suit-dashboard", "alert-dashboard"),
    ("ai-suit-visualizer", "alert-visualizer"),
    ("alert-aisuit", "alert-paper"),
    ("aigovsensing", "anonymous-org"),
    ("leemgs", "anonymous"),
    ("AISUIT", "ALERT"),
    ("aisuit", "alert"),
    ("ai-suit", "alert"),
    ("ai_suit", "alert"),
    # Dashboard CSV column "개요 및 배경 (By Gauss)": the model name can reveal affiliation.
    (" (By Gauss)", " (LLM-generated)"),
    ("By Gauss", "LLM-generated"),
]

DEFAULT_EXCLUDES = [
    ".git", ".git/*", "*/.git/*", "__pycache__", "*/__pycache__/*", "*.pyc",
    ".env", "*/.env", ".DS_Store", "*.log", "node_modules", "*/node_modules/*",
]
IMAGE_GLOBS = ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp", "*.svg"]
PDF_GLOBS = ["*.pdf"]

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# github.com/<user>/... but not api.github.com/repos/{owner} templates
GITHUB_USER_URL = re.compile(r"(?<!api\.)github\.com/(?!repos/)(?!\{)[A-Za-z0-9_-]+")
ALLOWED_EMAIL_HINTS = ("example.com", "example.org", "noreply")


def is_text(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:4096]
    except OSError:
        return False
    if b"\0" in chunk:
        return False
    try:
        chunk.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def excluded(rel: str, patterns: list[str]) -> bool:
    name = rel.rsplit("/", 1)[-1]
    return any(fnmatch.fnmatch(rel, p) or fnmatch.fnmatch(name, p) for p in patterns)


def apply_replacements(text: str, reps: list[tuple[str, str]], counts: dict) -> str:
    for old, new in reps:
        n = text.count(old)
        if n:
            counts[old] = counts.get(old, 0) + n
            text = text.replace(old, new)
    return text


def scan(out: Path, forbidden: list[str]) -> list[str]:
    findings = []
    for path in sorted(out.rglob("*")):
        rel = path.relative_to(out).as_posix()
        for term in forbidden:
            if term.lower() in rel.lower():
                findings.append(f"{rel}: path contains '{term}'")
        if not path.is_file() or not is_text(path):
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            low = line.lower()
            for term in forbidden:
                if term.lower() in low:
                    findings.append(f"{rel}:{i}: contains '{term}'")
            for m in EMAIL.finditer(line):
                if not any(h in m.group(0) for h in ALLOWED_EMAIL_HINTS):
                    findings.append(f"{rel}:{i}: e-mail address '{m.group(0)}'")
            for m in GITHUB_USER_URL.finditer(line):
                findings.append(f"{rel}:{i}: GitHub URL '{m.group(0)}'")
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", action="append", required=True, help="DIR or DIR:NAME (repeatable)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--replace", action="append", default=[], help="OLD=NEW (repeatable)")
    ap.add_argument("--forbid", action="append", default=[], help="extra term that must not remain")
    ap.add_argument("--exclude", action="append", default=[], help="extra glob to drop")
    ap.add_argument("--keep-images", action="store_true")
    ap.add_argument("--keep-pdfs", action="store_true")
    ap.add_argument("--zip", action="store_true", help="also write OUT.zip if the scan passes")
    args = ap.parse_args()

    reps = [tuple(r.split("=", 1)) for r in args.replace] + DEFAULT_REPLACEMENTS
    reps.sort(key=lambda kv: -len(kv[0]))
    excludes = DEFAULT_EXCLUDES + args.exclude
    if not args.keep_images:
        excludes += IMAGE_GLOBS
    if not args.keep_pdfs:
        excludes += PDF_GLOBS

    if args.out.exists():
        shutil.rmtree(args.out)
    args.out.mkdir(parents=True)

    counts: dict[str, int] = {}
    dropped: list[str] = []
    copied = 0
    for spec in args.src:
        src_s, _, name = spec.partition(":")
        src = Path(src_s).resolve()
        name = name or src.name
        name = apply_replacements(name, reps, counts)
        for path in sorted(src.rglob("*")):
            rel = path.relative_to(src).as_posix()
            if excluded(rel, excludes):
                if path.is_file():
                    dropped.append(f"{name}/{rel}")
                continue
            if not path.is_file():
                continue
            target = args.out / name / apply_replacements(rel, reps, counts)
            target.parent.mkdir(parents=True, exist_ok=True)
            if is_text(path):
                text = apply_replacements(path.read_text(encoding="utf-8"), reps, counts)
                target.write_text(text, encoding="utf-8")
            else:
                shutil.copyfile(path, target)
            copied += 1

    forbidden = [old for old, _ in DEFAULT_REPLACEMENTS] + [r.split("=", 1)[0] for r in args.replace] + args.forbid
    findings = scan(args.out, forbidden)

    report = ["# Anonymization report", "",
              f"- Files copied: {copied}", f"- Files dropped: {len(dropped)}", "",
              "## Replacements applied", ""]
    report += [f"- `{k}`: {v}" for k, v in sorted(counts.items())] or ["- none"]
    report += ["", "## Dropped files", ""] + ([f"- `{d}`" for d in dropped] or ["- none"])
    report += ["", "## Residual findings", ""] + ([f"- {f}" for f in findings] or ["- none: scan passed"])
    report += ["", "## Manual checks still required", "",
               "- Read every README and comment for names, affiliations, project history, or Slack/issue links.",
               "- Check that data files contain no internal identifiers (user names, internal URLs).",
               "- Search a few distinctive code strings on GitHub: if they match a public repository, "
               "make that repository private for the review period."]
    # The report names the original identifiers, so it must live OUTSIDE the
    # output tree (and therefore outside the zip).
    report_path = args.out.parent / f"{args.out.name}_ANONYMIZATION_REPORT.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"report: {report_path} (not included in the supplement)")

    print(f"copied {copied} files, dropped {len(dropped)}, residual findings: {len(findings)}")
    for f in findings[:30]:
        print("  " + f)
    if findings:
        print("scan FAILED: fix the sources or add --replace rules, then re-run.")
        return 1
    if args.zip:
        zpath = args.out.with_suffix(".zip")
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for p in sorted(args.out.rglob("*")):
                if p.is_file():
                    z.write(p, p.relative_to(args.out.parent).as_posix())
        print(f"wrote {zpath}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
