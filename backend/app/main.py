from fastapi import FastAPI
from app.retriever import answer_question

app = FastAPI()

@app.get("/health")
def health(): return {"ok": True}

@app.post("/ask")
async def ask(payload: dict):
    q = payload.get("query","")
    return await answer_question(q)
