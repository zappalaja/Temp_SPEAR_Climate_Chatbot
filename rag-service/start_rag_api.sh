#!/usr/bin/env bash
set -e

# --------------------------------------------------
# RAG configuration (container-friendly paths)
# Use environment variables or defaults
# --------------------------------------------------
export CHROMA_PERSIST_DIR="${CHROMA_PERSIST_DIR:-/app/chroma_db}"
export CHROMA_COLLECTION="${CHROMA_COLLECTION:-nougat_merged}"
export EMBED_MODEL="${EMBED_MODEL:-sentence-transformers/all-MiniLM-L6-v2}"

# --------------------------------------------------
# Start FastAPI
# --------------------------------------------------
exec uvicorn rag_service:app --host 0.0.0.0 --port 8002

