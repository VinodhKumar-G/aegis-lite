"""
AEGIS Lite — RAG Pipeline
Retrieval-Augmented Generation pipeline:
  1. Embed the user's question
  2. Search the local vector database for relevant memory chunks
  3. Combine retrieved chunks + question into a prompt
  4. Send to local LLM (Ollama) for answer generation
  5. Return answer WITH source citations

Everything happens locally. No network calls during inference.
"""

import json
from typing import List, Dict, Tuple
from pathlib import Path

import lancedb
import numpy as np

from aegis.config import (
    VECTOR_DIR,
    TOP_K_RETRIEVE,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)
from aegis.embeddings.engine import embed_query, embed_texts
from aegis.memory.store import MemoryStore
from aegis.llm.interface import ask_llm


# ── Vector Index ───────────────────────────────────────────────────────────────

def get_vector_db():
    """Connect to the local LanceDB vector database."""
    VECTOR_DIR.mkdir(parents=True, exist_ok=True)
    return lancedb.connect(str(VECTOR_DIR))


def build_index(store: MemoryStore) -> bool:
    """
    Build (or rebuild) the vector index from the memory store.
    Call this after adding new memories.

    Returns:
        True if index built successfully.
    """
    records = store.get_all_text()
    if not records:
        print("No records to index.")
        return False

    # Chunk each record's text
    chunks = []
    for record in records:
        text = record["text"]
        # Simple sliding window chunking
        words = text.split()
        chunk_words = CHUNK_SIZE // 5  # approximate words per chunk
        overlap_words = CHUNK_OVERLAP // 5

        i = 0
        while i < len(words):
            chunk_text = " ".join(words[i : i + chunk_words])
            chunks.append(
                {
                    "record_id": record["id"],
                    "kind": record["kind"],
                    "title": record["title"],
                    "chunk_text": chunk_text,
                    "chunk_index": i // chunk_words,
                }
            )
            i += chunk_words - overlap_words
            if i >= len(words):
                break

    # Embed all chunks
    texts = [c["chunk_text"] for c in chunks]
    print(f"Embedding {len(chunks)} chunks from {len(records)} records...")
    vectors = embed_texts(texts)

    # Build LanceDB table
    db = get_vector_db()
    table_name = "memory_chunks"

    # Drop existing table to rebuild
    if table_name in db.table_names():
        db.drop_table(table_name)

    # Prepare data for LanceDB
    data = [
        {
            "vector": vectors[i],
            "record_id": chunks[i]["record_id"],
            "kind": chunks[i]["kind"],
            "title": chunks[i]["title"],
            "chunk_text": chunks[i]["chunk_text"],
            "chunk_index": chunks[i]["chunk_index"],
        }
        for i in range(len(chunks))
    ]

    db.create_table(table_name, data=data)
    print(f"✓ Vector index built: {len(data)} chunks indexed")
    return True


def retrieve(query: str, top_k: int = TOP_K_RETRIEVE) -> List[Dict]:
    """
    Retrieve the most relevant memory chunks for a query.
    Uses semantic vector search (cosine similarity).

    Args:
        query: The user's natural language question
        top_k: Number of chunks to retrieve

    Returns:
        List of relevant chunks with metadata and similarity scores
    """
    db = get_vector_db()

    if "memory_chunks" not in db.table_names():
        return []

    table = db.open_table("memory_chunks")
    query_vector = embed_query(query)

    results = (
        table.search(query_vector)
        .limit(top_k)
        .to_list()
    )

    return results


# ── RAG Answer Generation ──────────────────────────────────────────────────────

def answer(query: str, store: MemoryStore) -> Dict:
    """
    Full RAG pipeline: retrieve → prompt → LLM → answer with citations.

    Args:
        query: The user's question in plain English
        store: The memory store (for keyword fallback)

    Returns:
        Dict with 'answer', 'sources', 'retrieved_chunks'
    """

    # Step 1: Semantic retrieval from vector DB
    vector_results = retrieve(query, top_k=TOP_K_RETRIEVE)

    # Step 2: Keyword fallback if vector search returns nothing
    keyword_results = []
    if not vector_results:
        keyword_results = store.keyword_search(query, limit=TOP_K_RETRIEVE)

    # Step 3: Assemble context from retrieved chunks
    context_parts = []
    sources = []

    for i, chunk in enumerate(vector_results):
        context_parts.append(
            f"[Source {i+1}: {chunk['title']} ({chunk['kind']})]"
            f"\n{chunk['chunk_text']}"
        )
        sources.append(
            {
                "title": chunk["title"],
                "kind": chunk["kind"],
                "chunk": chunk["chunk_text"][:100] + "...",
            }
        )

    for record in keyword_results:
        if record["id"] not in [c.get("record_id") for c in vector_results]:
            context_parts.append(
                f"[Source: {record['title']} ({record['kind']})]"
                f"\n{record['content'][:300]}"
            )
            sources.append(
                {
                    "title": record["title"],
                    "kind": record["kind"],
                    "chunk": record["content"][:100] + "...",
                }
            )

    # Step 4: Build the RAG prompt
    if not context_parts:
        return {
            "answer": (
                "I don't have any information about that in my memory yet. "
                "Please add some notes or meeting records first using the 'Add Memory' tab."
            ),
            "sources": [],
            "retrieved_chunks": [],
        }

    context_text = "\n\n---\n\n".join(context_parts)

    prompt = f"""You are AEGIS Lite, a private personal AI assistant.
You only answer from the personal memory provided below.
If the memory does not contain the answer, say "I don't have that information in my memory."
Never make up information. Always be specific and cite which source you used.

=== PERSONAL MEMORY ===
{context_text}
=== END OF MEMORY ===

Question: {query}

Answer (be concise, cite sources by their title):"""

    # Step 5: Get answer from local LLM
    llm_answer = ask_llm(prompt)

    return {
        "answer": llm_answer,
        "sources": sources,
        "retrieved_chunks": vector_results,
    }