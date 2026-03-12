#!/usr/bin/env python3
import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# --------- CONFIG (edit if needed) ----------
# Default path for containerized deployment; override with CHROMA_PERSIST_DIR env var
# For target system: CHROMA_PERSIST_DIR=/home/Jake.Zappala/SPEAR-RAG-Ingestion/chroma_db
PERSIST_DIR = os.environ.get(
    "CHROMA_PERSIST_DIR",
    "/app/chroma_db",
)

# MUST match what you used during ingestion
COLLECTION = os.environ.get("CHROMA_COLLECTION", "nougat_merged")

# MUST match what you used during ingestion
EMBED_MODEL = os.environ.get(
    "EMBED_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)

DEFAULT_K = int(os.environ.get("TOP_K", "5"))
# -------------------------------------------


app = FastAPI(title="SPEAR RAG Service", version="0.1.0")

_embeddings = None
_vectordb = None


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    k: int = Field(DEFAULT_K, ge=1, le=50)
    include_scores: bool = True


class RetrievedDoc(BaseModel):
    content: str
    metadata: Dict[str, Any]
    score: Optional[float] = None


class QueryResponse(BaseModel):
    query: str
    k: int
    results: List[RetrievedDoc]


def get_vectordb() -> Chroma:
    global _embeddings, _vectordb
    if _vectordb is None:
        if not os.path.isdir(PERSIST_DIR):
            raise RuntimeError(f"Chroma persist dir not found: {PERSIST_DIR}")

        _embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

        # This opens your existing persistent Chroma DB
        _vectordb = Chroma(
            collection_name=COLLECTION,
            persist_directory=PERSIST_DIR,
            embedding_function=_embeddings,
        )
    return _vectordb


@app.get("/health")
def health():
    try:
        db = get_vectordb()
        # lightweight call
        _ = db._collection.count()
        return {
            "ok": True,
            "persist_dir": PERSIST_DIR,
            "collection": COLLECTION,
            "embed_model": EMBED_MODEL,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    try:
        db = get_vectordb()

        if req.include_scores:
            docs_and_scores = db.similarity_search_with_score(req.query, k=req.k)
            results = [
                RetrievedDoc(content=d.page_content, metadata=d.metadata, score=float(s))
                for d, s in docs_and_scores
            ]
        else:
            docs = db.similarity_search(req.query, k=req.k)
            results = [RetrievedDoc(content=d.page_content, metadata=d.metadata) for d in docs]

        return QueryResponse(query=req.query, k=req.k, results=results)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
