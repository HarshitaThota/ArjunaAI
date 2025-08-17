import os
from typing import List, Dict, Any
from dotenv import load_dotenv; load_dotenv()
from pinecone import Pinecone
from openai import OpenAI
import cohere

INDEX = os.getenv("PINECONE_INDEX", "gita-rag")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(INDEX)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
co = cohere.Client(os.getenv("COHERE_API_KEY")) if os.getenv("COHERE_API_KEY") else None

SYSTEM = (
    "You answer using the Bhagavad Gita only. "
    "First give a short, neutral 2–3 sentence answer. "
    "Then list 2–3 supporting verses with chapter:verse in bullets. "
    "Do not invent quotes. If unsure, say so."
)

ANSWER_TMPL = """Question: {q}
Relevant verses:
{ctx}

Write a concise answer in 2–3 sentences.
Then add 2–3 bullet points: 'Chapter X:Verse Y — <short excerpt>'. Keep quotes verbatim."""

def _dense_search(q: str, k: int = 24) -> List[Dict[str, Any]]:
    emb = openai_client.embeddings.create(model="text-embedding-3-large", input=q).data[0].embedding
    res = index.query(vector=emb, top_k=k, include_metadata=True)
    docs = []
    for m in res.matches:
        md = m.metadata or {}
        text = md.get("eng_meaning") or md.get("transliteration") or ""
        docs.append({
            "id": m.id,
            "score": m.score,
            "chapter": md.get("chapter",""),
            "verse": md.get("verse",""),
            "text": text
        })
    return docs

def _rerank(q: str, docs: list[dict], top_n: int = 8) -> list[dict]:
    # No Cohere key? fall back to dense scores
    if not os.getenv("COHERE_API_KEY"):
        return sorted(docs, key=lambda d: d["score"], reverse=True)[:top_n]
    try:
        rr = co.rerank(
            model="rerank-english-v3.0",
            query=q,
            documents=[d["text"] for d in docs],
            top_n=top_n,
        )
        return [docs[r.index] for r in rr.results]
    except Exception as e:
        # Any error (401, network, etc.) -> safe fallback
        print(f"[rerank] falling back due to: {e}")
        return sorted(docs, key=lambda d: d["score"], reverse=True)[:top_n]


def _exact_verse_lookup(q: str) -> dict | None:
    import re
    m = re.match(r"^\s*(\d{1,2})\s*:\s*(\d{1,3})\s*$", q)
    if not m:
        return None
    vid = f"{int(m.group(1))}:{int(m.group(2))}"
    out = index.fetch(ids=[vid])

    # Newer clients: out.vectors is a dict[str, Vector]
    rec = None
    if hasattr(out, "vectors"):
        # Could be a dict, or an object with .get
        vectors = out.vectors
        if isinstance(vectors, dict):
            rec = vectors.get(vid)
        else:
            try:
                rec = vectors[vid]
            except Exception:
                pass
    # Fallback if fetch returns a plain dict-like
    if rec is None and isinstance(out, dict):
        rec = out.get("vectors", {}).get(vid)

    if rec is None:
        return None

    # Access metadata safely (object or dict)
    md = getattr(rec, "metadata", None)
    if md is None and isinstance(rec, dict):
        md = rec.get("metadata", {})
    if md is None:
        md = {}

    txt = md.get("eng_meaning") or md.get("transliteration") or ""
    return {
        "id": vid,
        "chapter": md.get("chapter", ""),
        "verse": md.get("verse", ""),
        "text": txt
    }

async def answer_question(q: str, top_k: int = 24, top_n: int = 8) -> Dict[str, Any]:
    # 0) exact verse short-circuit
    exact = _exact_verse_lookup(q)
    if exact:
        return {
            "answer": f"Verse {exact['id']} from the Bhagavad Gita:",
            "verses": [exact],
            "confidence": 0.95,
            "notes": "Exact-verse lookup."
        }

    # 1) retrieve
    docs = _dense_search(q, k=top_k)
    top = _rerank(q, docs, top_n=top_n)

    # 2) build context string
    ctx_lines = [f"- {t['id']}: {t['text']}" for t in top]
    ctx = "\n".join(ctx_lines) if ctx_lines else "(no relevant verses found)"

    # 3) LLM compose
    comp = openai_client.chat.completions.create(
        model=os.getenv("OPENAI_CHAT_MODEL","gpt-4o-mini"),
        messages=[
            {"role":"system","content": SYSTEM},
            {"role":"user","content": ANSWER_TMPL.format(q=q, ctx=ctx)}
        ]
    )
    answer = comp.choices[0].message.content

    # 4) basic confidence (simple, transparent)
    import statistics as stats
    dense_scores = [d["score"] for d in top] or [0.0]
    conf = min(0.99, max(0.3, (stats.mean(dense_scores))))

    return {
        "answer": answer,
        "verses": top,
        "confidence": conf,
        "notes": "Retrieved via embeddings, reranked (if enabled)."
    }
