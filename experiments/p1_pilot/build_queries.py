#!/usr/bin/env python3
"""Build masked citing-context queries (DESIGN.md §3).

Roles
  pre      opinion decided after A and before t (=B's date) citing A; gold = A
  post     opinion decided after t citing B; gold = B; stale = A
  control  opinion citing a case that appears nowhere in the overruled table,
           one per post query, matched on the citing decade; gold = that case
At most CAP_PER_ROLE queries per (pair, role), chosen with a fixed seed.
"""

from __future__ import annotations

import csv
import json
import random
import re
import sys
from collections import defaultdict

from p1lib import HERE, MIN_CHARS, OVERRULE_RE, WORK, doc_text, iter_corpus, mask, party_terms, passage_around

CAP_PER_ROLE = 5
SEED = 13


def find_cite(text: str, cite: str) -> int:
    i = text.find(cite)
    if i >= 0:
        return i
    pat = re.sub(r"\s+", r"\\s*", re.escape(cite).replace("\\ ", " "))
    m = re.search(pat, text)
    return m.start() if m else -1


def main() -> int:
    pairs = list(csv.DictReader(open(HERE / "data/pairs.csv", encoding="utf-8")))
    raw = list(csv.DictReader(open(HERE / "data/pairs_raw.csv", encoding="utf-8")))
    table_cites = {r["overruled_cite"] for r in raw} | {r["overruling_cite"] for r in raw if r["overruling_cite"]}

    meta = {}
    for r in iter_corpus():
        meta[r["id"]] = (r["date"], r["cite"], r["name"], len(doc_text(r)))
    names = {i: m[2] for i, m in meta.items()}

    # Earliest *full* overruling of each A over all matched table rows: a
    # pre-closure query must predate it, not only this pair's overruling date.
    first_close = {}
    for fname in ("pairs.csv", "pairs_excluded.csv"):
        for r in csv.DictReader(open(HERE / "data" / fname, encoding="utf-8")):
            if r.get("a_id") and r.get("b_date") and r["partial"] != "1":
                a = int(r["a_id"])
                first_close[a] = min(first_close.get(a, "9999"), r["b_date"])

    a_pairs = defaultdict(list)   # A id -> pair indices
    b_pairs = defaultdict(list)   # B id -> pair indices
    for k, p in enumerate(pairs):
        a_pairs[int(p["a_id"])].append(k)
        b_pairs[int(p["b_id"])].append(k)

    cands = defaultdict(list)     # (pair, role) -> candidate tuples
    control_pool = defaultdict(list)  # decade -> candidates
    for c in iter_corpus():
        cdate = c["date"]
        for e in c["cites_to"]:
            ids = set(e["case_ids"])
            op = e.get("opinion_index", 0)
            if op < 0 or op >= len(c["opinions"]):  # -1 = head matter
                continue
            hit = False
            for a in ids & a_pairs.keys():
                for k in a_pairs[a]:
                    p = pairs[k]
                    end = min(p["b_date"], first_close.get(a, "9999"))
                    if p["a_date"] < cdate < end and c["id"] != int(p["b_id"]):
                        cands[(k, "pre")].append((c["id"], op, e["cite"], a)); hit = True
            for b in ids & b_pairs.keys():
                for k in b_pairs[b]:
                    if cdate > pairs[k]["b_date"]:
                        cands[(k, "post")].append((c["id"], op, e["cite"], b)); hit = True
            if not hit and len(ids) == 1:
                t = next(iter(ids))
                m = meta.get(t)
                if m and m[1] and m[1] not in table_cites and m[3] >= MIN_CHARS and m[0] < cdate:
                    control_pool[cdate[:3]].append((c["id"], op, e["cite"], t))

    rng = random.Random(SEED)
    chosen = {}
    for key in sorted(cands):
        lst = sorted(set(cands[key]))
        rng.shuffle(lst)
        chosen[key] = lst

    # second pass: extract passages for every candidate we may need
    need = defaultdict(list)
    for key, lst in chosen.items():
        for cand in lst:
            need[cand[0]].append(("pair", key, cand))
    texts = {}
    for c in iter_corpus():
        if c["id"] in need and len(c["opinions"]) > len(texts.get(c["id"], [])):
            texts[c["id"]] = [o["text"] for o in c["opinions"]]

    queries, qid = [], 0
    post_by_decade = defaultdict(int)
    for (k, role), lst in sorted(chosen.items()):
        p = pairs[k]
        a, b = int(p["a_id"]), int(p["b_id"])
        terms_a, terms_b = party_terms(names[a]), party_terms(names[b])
        n = 0
        for cid, op, cite, target in lst:
            if n >= CAP_PER_ROLE:
                break
            if op >= len(texts.get(cid, [])):
                continue
            text = texts[cid][op]
            pos = find_cite(text, cite)
            if pos < 0:
                continue
            passage = passage_around(text, pos)
            if role == "post":
                a_cite_num = p["overruled_cite"].split(" U.S. ")
                mentions_a = re.search(rf"{a_cite_num[0]}\s*U\.\s?S\.\s*{a_cite_num[1]}\b", passage)
                if mentions_a or OVERRULE_RE.search(passage) or any(t.lower() in passage.lower() for t in terms_a):
                    continue
            q = mask(passage, terms_a + terms_b)
            if len(q.split()) < 8:
                continue
            queries.append({"qid": qid, "role": role, "pair": k, "t_q": meta[cid][0], "source_id": cid,
                            "gold_id": target, "stale_id": a if role == "post" else "", "a_id": a,
                            "partial": int(p["partial"]), "text": q})
            qid += 1
            n += 1
            if role == "post":
                post_by_decade[meta[cid][0][:3]] += 1

    # controls matched on citing decade, one per post query
    ctrl_texts_needed = {}
    picked = []
    for dec, cnt in sorted(post_by_decade.items()):
        pool = sorted(set(control_pool.get(dec, [])))
        rng.shuffle(pool)
        picked.append((dec, pool, cnt))
    need_ids = {c[0] for _, pool, cnt in picked for c in pool[: cnt * 4]}
    for c in iter_corpus():
        if c["id"] in need_ids and len(c["opinions"]) > len(ctrl_texts_needed.get(c["id"], [])):
            ctrl_texts_needed[c["id"]] = [o["text"] for o in c["opinions"]]
    for dec, pool, cnt in picked:
        n = 0
        for cid, op, cite, target in pool[: cnt * 4]:
            if n >= cnt:
                break
            if op >= len(ctrl_texts_needed.get(cid, [])):
                continue
            text = ctrl_texts_needed[cid][op]
            pos = find_cite(text, cite)
            if pos < 0:
                continue
            q = mask(passage_around(text, pos), party_terms(names[target]))
            if len(q.split()) < 8:
                continue
            queries.append({"qid": qid, "role": "control", "pair": f"c{dec}", "t_q": meta[cid][0],
                            "source_id": cid, "gold_id": target, "stale_id": "", "a_id": "",
                            "partial": 0, "text": q})
            qid += 1
            n += 1

    WORK.mkdir(parents=True, exist_ok=True)
    with open(WORK / "queries.jsonl", "w", encoding="utf-8") as f:
        for q in queries:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    roles = defaultdict(int)
    for q in queries:
        roles[q["role"]] += 1
    pairs_with_post = len({q["pair"] for q in queries if q["role"] == "post"})
    print(f"{len(queries)} queries {dict(roles)}; pairs with >=1 post query: {pairs_with_post}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
