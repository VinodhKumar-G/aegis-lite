-- AEGIS Lite — Episodic Memory Schema
-- Stores every note, meeting, task, deadline the user feeds in.

CREATE TABLE IF NOT EXISTS memory_records (
    id          TEXT    PRIMARY KEY,
    kind        TEXT    NOT NULL,           -- 'note' | 'meeting' | 'task' | 'deadline'
    title       TEXT    NOT NULL,
    content     TEXT    NOT NULL,           -- Raw text content
    created_at  INTEGER NOT NULL,           -- Unix timestamp
    source      TEXT    DEFAULT 'user',     -- Where it came from
    tags        TEXT    DEFAULT '[]'        -- JSON array of tags
);

-- Full-text search index for BM25 keyword search
CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts
    USING fts5(title, content, content='memory_records', content_rowid='rowid');

-- Trigger to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS memory_fts_insert
    AFTER INSERT ON memory_records BEGIN
        INSERT INTO memory_fts(rowid, title, content)
        VALUES (new.rowid, new.title, new.content);
    END;

CREATE TRIGGER IF NOT EXISTS memory_fts_delete
    BEFORE DELETE ON memory_records BEGIN
        INSERT INTO memory_fts(memory_fts, rowid, title, content)
        VALUES ('delete', old.rowid, old.title, old.content);
    END;