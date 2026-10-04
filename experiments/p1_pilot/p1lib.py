"""Shared helpers for the P1 pilot: corpus loading, passages, masking, metrics."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE / "data" / "work"
MIN_CHARS = 1000  # substantive opinions only (fixed before any retrieval run)

# ---------------------------------------------------------------- corpus


def iter_corpus(path: Path = WORK / "corpus.jsonl"):
    with open(path, encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def doc_text(rec: dict) -> str:
    return "\n".join(o["text"] for o in rec["opinions"])


# ---------------------------------------------------------------- sentences

_ABBREV = [
    "v.", "vs.", "U. S.", "U.S.", "S. Ct.", "L. Ed.", "Ed.", "Inc.", "Co.", "Corp.", "Ltd.",
    "No.", "Nos.", "Id.", "id.", "Ibid.", "e.g.", "i.e.", "cf.", "Cf.", "Mr.", "Mrs.", "Ms.",
    "Dr.", "St.", "Ct.", "App.", "Supp.", "Cong.", "Sess.", "Stat.", "Rev.", "J.", "JJ.",
    "C. J.", "art.", "Art.", "ch.", "cl.", "pp.", "p.", "n.", "nn.", "Cir.", "Dist.", "Gen.",
    "Comm'n.", "Dept.", "Assn.", "Bros.", "Wall.", "How.", "Pet.", "Wheat.", "Dall.", "Cr.",
    "F.", "Fed.", "Reg.", "Jr.", "Sr.", "seq.", "ed.", "Am.", "Mass.", "Pa.", "Cal.", "Ill.",
]
_PROTECT = "⁣"  # invisible separator used to hide protected periods


def split_sentences(text: str) -> list[tuple[int, int]]:
    """Return (start, end) spans of sentences, protecting legal abbreviations."""
    prot = text
    for ab in _ABBREV:
        prot = prot.replace(ab, ab.replace(".", _PROTECT))
    prot = re.sub(r"\b([A-Z])\.", lambda m: m.group(1) + _PROTECT, prot)  # initials
    spans, start = [], 0
    for m in re.finditer(r"[.?!][\"'”’)]*\s+(?=[A-Z\"“(\[])", prot):
        spans.append((start, m.end()))
        start = m.end()
    if start < len(text):
        spans.append((start, len(text)))
    return spans


def passage_around(text: str, pos: int, width: int = 1) -> str:
    spans = split_sentences(text)
    for i, (s, e) in enumerate(spans):
        if s <= pos < e:
            lo, hi = max(0, i - width), min(len(spans), i + width + 1)
            return text[spans[lo][0]:spans[hi - 1][1]].strip()
    return text[max(0, pos - 300): pos + 300].strip()


# ---------------------------------------------------------------- masking

_REPORTER = (r"U\.\s?S\.|S\.\s?Ct\.|L\.\s?Ed\.(?:\s?2d)?|F\.(?:\s?[23]d)?|F\.\s?Supp\.(?:\s?[23]d)?"
             r"|Wall\.|How\.|Pet\.|Cranch|Cr\.|Wheat\.|Dall\.|Black|Otto")
CITE_RE = re.compile(rf"\b\d+\s+(?:\((?:\d+\s+)?[A-Za-z.\s]+\)\s+)?(?:{_REPORTER})\s+\d+(?:,\s*\d+(?:[-–]\d+)?)*")
YEAR_RE = re.compile(r"\b(1[6-9]\d\d|20\d\d)\b")
CASE_RE = re.compile(
    r"(?:[A-Z][\w.'’&-]*(?:\s+(?:of|the|and|ex|rel\.|for|de|&)?\s*[A-Z][\w.'’&-]*){0,6})"
    r"\s+v\.\s+(?:[A-Z][\w.'’&-]*(?:\s+(?:of|the|and|for|de|&)?\s*[A-Z][\w.'’&-]*){0,6})")
GENERIC_PARTIES = {
    "united states", "state", "states", "commissioner", "people", "commonwealth", "city",
    "county", "board", "secretary", "attorney general", "united states of america",
}
OVERRULE_RE = re.compile(r"overrul|abrogat|no longer good law|disapprov|repudiat", re.I)


def party_terms(name: str) -> list[str]:
    terms = []
    for party in re.split(r"\s+v\.\s+", name or ""):
        party = re.sub(r"[,;]+$", "", party.strip())
        if len(party) >= 4 and party.lower() not in GENERIC_PARTIES:
            terms.append(party)
    return terms


def mask(text: str, extra_terms: list[str] = ()) -> str:
    out = CASE_RE.sub("[CASE]", text)
    for t in sorted(set(extra_terms), key=len, reverse=True):
        out = re.sub(re.escape(t), "[CASE]", out, flags=re.I)
    out = CITE_RE.sub("[CITE]", out)
    out = YEAR_RE.sub("[YEAR]", out)
    return re.sub(r"\s+", " ", out).strip()


# ---------------------------------------------------------------- metrics


def rank_of(ranked: list[int], target: int) -> int | None:
    try:
        return ranked.index(target) + 1
    except ValueError:
        return None


def ndcg_at(ranked: list[int], target: int, k: int = 10) -> float:
    r = rank_of(ranked[:k], target)
    return 1.0 / math.log2(r + 1) if r else 0.0


def recall_at(ranked: list[int], target: int, k: int = 10) -> float:
    return 1.0 if target in ranked[:k] else 0.0


def mrr(ranked: list[int], target: int) -> float:
    r = rank_of(ranked, target)
    return 1.0 / r if r else 0.0
