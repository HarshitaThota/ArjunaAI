import os, re
from typing import List, Dict, Any
from dotenv import load_dotenv; load_dotenv()
from pinecone import Pinecone
from openai import OpenAI

INDEX = os.getenv("PINECONE_INDEX", "gita-rag")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(INDEX)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM = (
    "You answer using only the Bhagavad Gita corpus provided in the context."
    " Write a DIRECT ANSWER in AT MOST 4 SENTENCES. No more."
    "Try to give a related verse existing in the context."
    " Do not invent quotes or verses. If unsure or off-topic, say so in one sentence."
)

ANSWER_TMPL = """Question: {q}
Relevant verses (chapter:verse — text):
{ctx}

Rules:
- Answer in AT MOST 4 SENTENCES (strict).
- Do not include Sanskrit in the answer body.
- Try to find a relevant verse, but if none exist, write the 4-sentence answer only (no verse section).
Now write the answer:"""

def _dense_search(q: str, k: int = 20) -> List[Dict[str, Any]]:
    emb = openai_client.embeddings.create(model="text-embedding-3-large", input=q).data[0].embedding
    res = index.query(vector=emb, top_k=k, include_metadata=True)
    docs = []
    for m in res.matches:
        md = m.metadata or {}
        docs.append({
            "id": m.id,
            "score": float(m.score or 0.0),
            "chapter": md.get("chapter",""),
            "verse": md.get("verse",""),
            "english": md.get("eng_meaning") or "",
            "transliteration": md.get("transliteration") or "",
            "sanskrit": md.get("shloka_sanskrit") or "",
            "text": (md.get("eng_meaning") or md.get("transliteration") or "")
        })
    return docs

def _exact_verse_lookup(q: str) -> Dict[str, Any] | None:
    m = re.match(r"^\s*(\d{1,2})\s*:\s*(\d{1,3})\s*$", q)
    if not m: return None
    vid = f"{int(m.group(1))}:{int(m.group(2))}"
    out = index.fetch(ids=[vid])
    rec = (getattr(out, "vectors", None) or {}).get(vid)
    if not rec: return None
    md = rec.get("metadata", {}) if isinstance(rec, dict) else getattr(rec, "metadata", {}) or {}
    return {
        "id": vid,
        "chapter": md.get("chapter",""),
        "verse": md.get("verse",""),
        "english": md.get("eng_meaning") or "",
        "transliteration": md.get("transliteration") or "",
        "sanskrit": md.get("shloka_sanskrit") or ""
    }

def _four_sentences_max(text: str) -> str:
    # hard-stop after four sentences
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return " ".join(parts[:4]).strip()

async def answer_question(q: str, top_k: int = 20, top_n: int = 5) -> Dict[str, Any]:
    # 0) exact verse mode
    exact = _exact_verse_lookup(q)
    if exact:
        # Just present that verse; summary can mention it
        summary = f"Verse {exact['chapter']}:{exact['verse']} from the Bhagavad Gita."
        return {
            "summary": summary,
            "verses": [exact],              # include english + transliteration; UI can reveal sanskrit
            "confidence": 0.95,
            "notes": "Exact-verse lookup"
        }

    # 1) retrieves (dense no rerank)
    docs = _dense_search(q, k=top_k)
    top = sorted(docs, key=lambda d: d["score"], reverse=True)[:top_n]

    # 2) builds context for LLM
    ctx = "\n".join([f"- {t['id']}: {t['text']}" for t in top]) if top else "(none)"

    # 3) composes answer 
    comp = openai_client.chat.completions.create(
        model=os.getenv("OPENAI_CHAT_MODEL","gpt-4o-mini"),
        messages=[{"role":"system","content": SYSTEM},
                  {"role":"user","content": ANSWER_TMPL.format(q=q, ctx=ctx)}]
    )
    summary = _four_sentences_max(comp.choices[0].message.content or "")

    # 4) decide if verses should be returned (if the best similarity is low, don't return verses)
    best = top[0]["score"] if top else 0.0
    VERSE_SCORE_THRESHOLD = 0.30  # I can adjust if needed (cosine similarity scale)
    verses = []
    if best >= VERSE_SCORE_THRESHOLD:
        # returns only the top 1–3 distinct verses
        for t in top[:3]:
            verses.append({
                "id": t["id"],
                "chapter": t["chapter"],
                "verse": t["verse"],
                "english": t["english"],
                "transliteration": t["transliteration"],
                "sanskrit": t["sanskrit"]
            })

    return {
        "summary": summary,
        "verses": verses,         
        "confidence": float(best),
        "notes": "Dense retrieval only; no rerank."
    }
