from fastapi import FastAPI
from pydantic import BaseModel
from app.retriever import answer_question

app = FastAPI()

class AskIn(BaseModel):
    query: str
    top_k: int | None = 24
    top_n: int | None = 8

@app.get("/health")
def health(): return {"ok": True}

@app.post("/ask")
async def ask(body: AskIn):
    return await answer_question(body.query, top_k=body.top_k, top_n=body.top_n)
