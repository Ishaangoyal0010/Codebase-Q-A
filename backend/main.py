from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from indexer import index_repo
from retriever import retrieve
from llm import ask_llm

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


class IndexRequest(BaseModel):
    repo_url: str


class AskRequest(BaseModel):
    question: str
    top_k: int = 6


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/index")
def index(req: IndexRequest):
    try:
        stats = index_repo(req.repo_url)
        return {"message": "done", **stats}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/ask")
def ask(req: AskRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question is empty")

    import indexer
    if indexer.vector_store is None:
        raise HTTPException(status_code=400, detail="no repo indexed yet, call /index first")

    chunks = retrieve(req.question, top_k=req.top_k)
    if not chunks:
        raise HTTPException(status_code=404, detail="no relevant code found")

    result = ask_llm(req.question, chunks)
    return result
