"""
AEGIS Lite — Central Configuration
All settings in one place. Easy to change for the demo.
"""

import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent.parent
DATA_DIR    = BASE_DIR / "data"
DB_PATH     = DATA_DIR / "db" / "aegis_memory.db"
VECTOR_DIR  = DATA_DIR / "vectors"

# ── LLM (via Ollama) ──────────────────────────────────────────────────────────
# phi3:mini  → ~2.3 GB  → fast in Codespaces (recommended for demo)
# llama3:8b  → ~4.7 GB  → better quality (use if machine has ≥16 GB RAM)
OLLAMA_MODEL    = os.getenv("AEGIS_MODEL", "phi3:mini")
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL",  "http://localhost:11434")
LLM_TEMPERATURE = 0.1     # Low = factual, grounded answers
LLM_MAX_TOKENS  = 512

# ── Embeddings ────────────────────────────────────────────────────────────────
# BGE-small: 380 MB, 384 dimensions, runs fast on CPU
EMBED_MODEL      = "BAAI/bge-small-en-v1.5"
EMBED_DIMENSIONS = 384

# ── RAG ───────────────────────────────────────────────────────────────────────
TOP_K_RETRIEVE = 5    # How many memory chunks to retrieve per query
CHUNK_SIZE     = 256  # Characters per chunk when indexing
CHUNK_OVERLAP  = 32   # Overlap between chunks

# ── Privacy ───────────────────────────────────────────────────────────────────
# This flag enforces that NO external network calls are made for inference.
# Ollama + local embeddings = fully offline after model download.
OFFLINE_MODE = True

# ── App ───────────────────────────────────────────────────────────────────────
APP_TITLE  = "AEGIS Lite"
APP_SLOGAN = "Your AI. Your Device. Your Data."