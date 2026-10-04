#!/usr/bin/env python3
"""Run an unmodified host retriever and write its top-100 per query.

Hosts (DESIGN.md §4):
  bm25       BM25 over full opinion text (k1=0.9, b=0.4, Pyserini defaults)
  bge        BAAI/bge-small-en-v1.5, 512-token chunks, doc score = max chunk sim
  legalbert  nlpaueb/legal-bert-base-uncased, mean pooling, same chunking

Candidates for a query are opinions decided strictly before the query date
(the index "as of" t_q), excluding the citing opinion itself. This applies to
every condition alike and is not part of the gate.

Output: runs/<host>.jsonl  {qid, docs: [[doc_id, score], ...]}
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np

from p1lib import HERE, MIN_CHARS, WORK, doc_text, iter_corpus

RUNS = HERE / "runs"
TOPK = 100
MASK_TOKENS = {"case", "cite", "year"}
TOKEN = re.compile(r"[a-z0-9]{2,}")


def load_docs():
    ids, dates, texts = [], [], []
    seen = set()
    for r in iter_corpus():
        t = doc_text(r)
        if len(t) >= MIN_CHARS and r["id"] not in seen:
            seen.add(r["id"])
            ids.append(r["id"]); dates.append(r["date"]); texts.append(t)
    return np.array(ids), np.array(dates), texts


def load_queries():
    return [json.loads(l) for l in open(WORK / "queries.jsonl", encoding="utf-8")]


def topk_filtered(scores: np.ndarray, ids, dates, q) -> list:
    s = scores.astype(np.float64).copy()
    s[dates >= q["t_q"]] = -np.inf
    s[ids == q["source_id"]] = -np.inf
    k = min(TOPK, int(np.isfinite(s).sum()))
    top = np.argpartition(-s, k - 1)[:k]
    top = top[np.argsort(-s[top])]
    return [[int(ids[i]), float(s[i])] for i in top]


# ------------------------------------------------------------------ BM25

def run_bm25(ids, dates, texts, queries, k1=0.9, b=0.4):
    from sklearn.feature_extraction.text import CountVectorizer
    vec = CountVectorizer(token_pattern=r"(?u)\b[a-z0-9]{2,}\b", lowercase=True, dtype=np.float32)
    tf = vec.fit_transform(texts).tocsc()
    n_docs = tf.shape[0]
    dl = np.asarray(tf.sum(axis=1)).ravel()
    avgdl = dl.mean()
    df = np.diff(tf.indptr)
    idf = np.log(1 + (n_docs - df + 0.5) / (df + 0.5))
    norm = k1 * (1 - b + b * dl / avgdl)
    vocab = vec.vocabulary_
    out = []
    for q in queries:
        terms = [t for t in TOKEN.findall(q["text"].lower()) if t not in MASK_TOKENS]
        cols = sorted({vocab[t] for t in terms if t in vocab})
        scores = np.zeros(n_docs, dtype=np.float64)
        for j in cols:
            start, end = tf.indptr[j], tf.indptr[j + 1]
            rows, f = tf.indices[start:end], tf.data[start:end]
            scores[rows] += idf[j] * f * (k1 + 1) / (f + norm[rows])
        out.append({"qid": q["qid"], "docs": topk_filtered(scores, ids, dates, q)})
    return out


# ------------------------------------------------------------------ dense

MODELS = {
    "bge": ("BAAI/bge-small-en-v1.5", "cls", "Represent this sentence for searching relevant passages: "),
    "legalbert": ("nlpaueb/legal-bert-base-uncased", "mean", ""),
}


def encode(model, tok, texts, pooling, batch, maxlen=512):
    import torch
    vecs = []
    with torch.inference_mode():
        for i in range(0, len(texts), batch):
            enc = tok(texts[i:i + batch], padding=True, truncation=True, max_length=maxlen, return_tensors="pt")
            out = model(**enc).last_hidden_state
            if pooling == "cls":
                v = out[:, 0]
            else:
                m = enc["attention_mask"].unsqueeze(-1).float()
                v = (out * m).sum(1) / m.sum(1)
            vecs.append(torch.nn.functional.normalize(v, dim=-1).numpy())
    return np.concatenate(vecs)


def chunk_doc(tok, text, n_chunks, size=510):
    ids = tok(text, add_special_tokens=False, truncation=False)["input_ids"][: n_chunks * size]
    return [tok.decode(ids[i:i + size]) for i in range(0, len(ids), size)] or [""]


def run_dense(host, ids, dates, texts, queries, n_chunks, batch):
    import torch
    from transformers import AutoModel, AutoTokenizer
    torch.set_num_threads(4)
    name, pooling, qprefix = MODELS[host]
    tok = AutoTokenizer.from_pretrained(name)
    model = AutoModel.from_pretrained(name).eval()
    cache = WORK / f"emb_{host}_k{n_chunks}.npz"
    if cache.exists():
        z = np.load(cache)
        emb, owner = z["emb"], z["owner"]
    else:
        chunks, owner = [], []
        for d, t in enumerate(texts):
            for c in chunk_doc(tok, t, n_chunks):
                chunks.append(c); owner.append(d)
        owner = np.array(owner)
        t0 = time.time()
        emb = encode(model, tok, chunks, pooling, batch)
        print(f"encoded {len(chunks)} chunks in {time.time() - t0:.0f}s", flush=True)
        np.savez(cache, emb=emb, owner=owner)
    qv = encode(model, tok, [qprefix + q["text"] for q in queries], pooling, batch)
    out = []
    n_docs = len(ids)
    for q, v in zip(queries, qv):
        sims = emb @ v
        doc_scores = np.full(n_docs, -np.inf)
        np.maximum.at(doc_scores, owner, sims)
        out.append({"qid": q["qid"], "docs": topk_filtered(doc_scores, ids, dates, q)})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", choices=["bm25", "bge", "legalbert"], required=True)
    ap.add_argument("--chunks", type=int, default=4, help="first N 512-token chunks per opinion (dense)")
    ap.add_argument("--batch", type=int, default=32)
    args = ap.parse_args()
    ids, dates, texts = load_docs()
    queries = load_queries()
    print(f"{len(ids)} docs, {len(queries)} queries, host={args.host}", flush=True)
    t0 = time.time()
    if args.host == "bm25":
        runs = run_bm25(ids, dates, texts, queries)
    else:
        runs = run_dense(args.host, ids, dates, texts, queries, args.chunks, args.batch)
    RUNS.mkdir(exist_ok=True)
    with open(RUNS / f"{args.host}.jsonl", "w") as f:
        for r in runs:
            f.write(json.dumps(r) + "\n")
    print(f"done in {time.time() - t0:.0f}s -> runs/{args.host}.jsonl")
    return 0


if __name__ == "__main__":
    sys.exit(main())
