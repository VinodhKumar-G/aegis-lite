"""
AEGIS Lite — Episodic Memory Store
Stores and retrieves personal notes, meetings, tasks, deadlines
in a local SQLite database. No cloud. No network.
"""

import sqlite3
import json
import uuid
import time
from pathlib import Path
from typing import List, Dict, Optional

from aegis.config import DB_PATH


class MemoryStore:
    """
    Local SQLite-based episodic memory.
    Stores everything the user tells AEGIS about their life.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize the database schema."""
        schema_path = Path(__file__).parent / "schema.sql"
        schema = schema_path.read_text()
        with self._conn() as conn:
            conn.executescript(schema)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    # ── Write ──────────────────────────────────────────────────────────────────

    def add(
        self,
        content: str,
        kind: str = "note",
        title: str = "",
        tags: List[str] = None,
        source: str = "user",
    ) -> str:
        """
        Add a memory record.

        Args:
            content: The text content (meeting notes, task description, etc.)
            kind: Type — 'note', 'meeting', 'task', 'deadline'
            title: Short title for the record
            tags: Optional list of tags e.g. ['project-alpha', 'urgent']
            source: Where this came from ('user', 'file', 'meeting')

        Returns:
            The UUID of the new record.
        """
        record_id = str(uuid.uuid4())
        if not title:
            # Auto-generate title from first line
            title = content.split("\n")[0][:60].strip()

        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO memory_records
                    (id, kind, title, content, created_at, source, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record_id,
                    kind,
                    title,
                    content,
                    int(time.time()),
                    source,
                    json.dumps(tags or []),
                ),
            )
        return record_id

    # ── Read ───────────────────────────────────────────────────────────────────

    def get_all(self, kind: Optional[str] = None) -> List[Dict]:
        """Get all memory records, optionally filtered by kind."""
        with self._conn() as conn:
            if kind:
                rows = conn.execute(
                    "SELECT * FROM memory_records WHERE kind=? ORDER BY created_at DESC",
                    (kind,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM memory_records ORDER BY created_at DESC"
                ).fetchall()
        return [dict(r) for r in rows]

    def get(self, record_id: str) -> Optional[Dict]:
        """Get a single record by ID."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM memory_records WHERE id=?", (record_id,)
            ).fetchone()
        return dict(row) if row else None

    def keyword_search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        BM25 full-text keyword search using SQLite FTS5.
        Sanitizes input to remove characters that break FTS5 syntax.
        """

        # ── Sanitize the query ─────────────────────────────────────────
        # FTS5 special characters that cause syntax errors:
        # ? * " ( ) - ^ : NOT AND OR
        # Strategy: strip punctuation, keep only plain words

        import re

        # Remove all non-alphanumeric characters except spaces
        clean = re.sub(r"[^\w\s]", " ", query)

        # Collapse multiple spaces
        clean = re.sub(r"\s+", " ", clean).strip()

        # Extract individual words
        words = clean.split()

        # If nothing usable remains after cleaning — return empty
        if not words:
            return []

        # Build FTS5 query — each word searched independently with OR
        # "meeting OR deadline OR tasks" style
        # More forgiving than exact phrase match
        fts_query = " OR ".join(words)

        # ── Run the search ─────────────────────────────────────────────
        try:
            with self._conn() as conn:
                rows = conn.execute(
                    """
                    SELECT m.*, rank
                    FROM memory_fts
                    JOIN memory_records m ON memory_fts.rowid = m.rowid
                    WHERE memory_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (fts_query, limit),
                ).fetchall()
            return [dict(r) for r in rows]

        except Exception as e:
            # If FTS still fails for any reason — fail silently
            # RAG will still work via vector search
            print(f"[keyword_search] FTS5 error ignored: {e}")
            return []

    def count(self) -> int:
        """Return total number of memory records."""
        with self._conn() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM memory_records"
            ).fetchone()[0]

    def delete(self, record_id: str) -> bool:
        """Delete a memory record by ID."""
        with self._conn() as conn:
            conn.execute(
                "DELETE FROM memory_records WHERE id=?", (record_id,)
            )
        return True

    def get_all_text(self) -> List[Dict]:
        """
        Return all records as list of dicts with id and full text.
        Used by the ingest pipeline to build the vector index.
        """
        records = self.get_all()
        return [
            {
                "id": r["id"],
                "text": f"[{r['kind'].upper()}] {r['title']}\n{r['content']}",
                "kind": r["kind"],
                "title": r["title"],
                "created_at": r["created_at"],
            }
            for r in records
        ]