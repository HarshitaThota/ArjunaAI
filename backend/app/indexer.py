import os
import time
import math
import pandas as pd
from typing import List, Dict, Any

from dotenv import load_dotenv; load_dotenv()
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

# ---- Config ----
INDEX_NAME = os.getenv("PINECONE_INDEX", "gita-rag")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT", "us-east1-gcp")
CSV_PATH = os.path.join(os.path.dirname(__file__), "data", os.getenv("GITA_CSV", "Bhagwad_Gita.csv"))
EMBED_MODEL = "text-embedding-3-large"   # 3072-dim

# ---- Clients ----
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---- Ensure index exists ----
existing = [i.name for i in pc.list_indexes()]
if INDEX_NAME not in existing:
    print(f"Creating Pinecone index '{INDEX_NAME}' ...")
    pc.create_index(
        name=INDEX_NAME,
        dimension=3072,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
index = pc.Index(INDEX_NAME)

# ---- Load CSV ----
if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"CSV not found at {CSV_PATH}")

df = pd.read_csv(CSV_PATH)
# Normalize expected columns
required = ["ID","Chapter","Verse","Shloka","Transliteration","HinMeaning","EngMeaning","WordMeaning"]
missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"CSV missing columns: {missing}")

# Clean up NaNs → empty strings
for c in required:
    df[c] = df[c].fillna("").astype(str)

# Helper: build the text we embed per verse
def build_embed_text(row: pd.Series) -> str:
    # Primary: English meaning; fallback to transliteration + word meaning
    english = row["EngMeaning"].strip()
    if not english:
        english = f"{row['Transliteration'].strip()} — {row['WordMeaning'].strip()}"
    # Add lightweight identifiers to help retrieval
    ch, vs = row["Chapter"].strip(), row["Verse"].strip()
    return f"Chapter {ch}, Verse {vs}: {english}"

def embed_batch(texts: List[str]) -> List[List[float]]:
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]

# Build vectors in batches
BATCH = 64
total = len(df)
print(f"Indexing {total} verses into Pinecone index '{INDEX_NAME}' ...")

for start in range(0, total, BATCH):
    batch = df.iloc[start:start+BATCH]

    inputs = [build_embed_text(r) for _, r in batch.iterrows()]
    embs = embed_batch(inputs)

    vectors: List[Dict[str, Any]] = []
    for j, (_, r) in enumerate(batch.iterrows()):
        # Stable ID like "2:47" (Chapter:Verse). Use dataset ID as fallback.
        ch = r["Chapter"].strip()
        vs = r["Verse"].strip()
        vid = f"{ch}:{vs}" if ch and vs else r["ID"].strip()

        metadata = {
            "id_dataset": r["ID"].strip(),
            "chapter": ch,
            "verse": vs,
            "shloka_sanskrit": r["Shloka"].strip(),
            "transliteration": r["Transliteration"].strip(),
            "hin_meaning": r["HinMeaning"].strip(),
            "eng_meaning": r["EngMeaning"].strip(),
            "word_meaning": r["WordMeaning"].strip(),
            "source": "kaggle_bhagavad_gita_a2m2a2n2"
        }
        vectors.append({
            "id": vid,
            "values": embs[j],
            "metadata": metadata
        })

    # Upsert this batch
    index.upsert(vectors=vectors)
    done = min(start + BATCH, total)
    print(f"Upserted {done}/{total}")

    # gentle pacing to avoid rate spikes
    time.sleep(0.1)

# Print index stats
try:
    stats = index.describe_index_stats()
    print("Done. Index stats:", stats)
except Exception as e:
    print("Indexed, but stats unavailable:", e)
