"""
AEGIS Lite — Ingest Pipeline
Takes user input (text, file content) → stores in memory → rebuilds vector index.
This is how you "teach" AEGIS about your life.
"""

from pathlib import Path
from typing import Optional

from aegis.memory.store import MemoryStore
from aegis.rag.pipeline import build_index


def ingest_text(
    content: str,
    kind: str = "note",
    title: str = "",
    tags: list = None,
    store: Optional[MemoryStore] = None,
    rebuild_index: bool = True,
) -> dict:
    """
    Ingest a piece of text into AEGIS memory.

    Args:
        content: The text to remember
        kind: 'note' | 'meeting' | 'task' | 'deadline'
        title: Short title (auto-generated if empty)
        tags: Optional tags
        store: MemoryStore instance (creates new one if None)
        rebuild_index: If True, rebuild the vector index immediately

    Returns:
        Dict with 'success', 'record_id', 'message'
    """
    if not content or not content.strip():
        return {"success": False, "record_id": None, "message": "Content is empty."}

    if store is None:
        store = MemoryStore()

    record_id = store.add(
        content=content.strip(),
        kind=kind,
        title=title,
        tags=tags or [],
    )

    if rebuild_index:
        build_index(store)

    return {
        "success": True,
        "record_id": record_id,
        "message": f"✓ Added to memory as '{kind}': {title or content[:40]}...",
    }


def ingest_file(
    file_path: str,
    kind: str = "note",
    store: Optional[MemoryStore] = None,
) -> dict:
    """
    Ingest a text file into AEGIS memory.
    Only .txt and .md files are supported.

    Args:
        file_path: Path to the text file
        kind: Memory kind to assign
        store: MemoryStore instance

    Returns:
        Dict with 'success', 'record_id', 'message'
    """
    path = Path(file_path)

    if not path.exists():
        return {"success": False, "record_id": None, "message": f"File not found: {file_path}"}

    if path.suffix.lower() not in [".txt", ".md"]:
        return {
            "success": False,
            "record_id": None,
            "message": "Only .txt and .md files are supported.",
        }

    content = path.read_text(encoding="utf-8")
    title = path.stem.replace("_", " ").replace("-", " ").title()

    return ingest_text(
        content=content,
        kind=kind,
        title=title,
        store=store,
        rebuild_index=True,
    )