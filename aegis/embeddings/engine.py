"""
AEGIS Lite — Local Embedding Engine
Uses BGE-small-en-v1.5 (~380 MB) to convert text into 384-dim vectors.
Runs 100% locally. No API call. No data leaves the device.
"""

from typing import List
from functools import lru_cache

from llama_index.embeddings.huggingface import HuggingFaceEmbedding

from aegis.config import EMBED_MODEL


@lru_cache(maxsize=1)
def get_embed_model() -> HuggingFaceEmbedding:
    """
    Load the embedding model once and cache it.
    BGE-small runs on CPU — no GPU needed.
    First call downloads the model (~380 MB) from HuggingFace.
    Subsequent calls use the cached version.
    """
    print(f"Loading embedding model: {EMBED_MODEL}")
    return HuggingFaceEmbedding(
        model_name=EMBED_MODEL,
        embed_batch_size=32,
    )


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Convert a list of text strings into embedding vectors.

    Args:
        texts: List of text strings to embed

    Returns:
        List of 384-dimensional float vectors
    """
    model = get_embed_model()
    return model.get_text_embedding_batch(texts)


def embed_query(query: str) -> List[float]:
    """
    Embed a single query string.
    BGE models perform better with this prefix for queries.
    """
    model = get_embed_model()
    # BGE-small works best with "Represent this sentence:" prefix for queries
    return model.get_query_embedding(f"Represent this sentence: {query}")