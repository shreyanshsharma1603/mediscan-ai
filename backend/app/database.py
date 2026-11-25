from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

from app.config import DB_PATH


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    target = db_path or DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


@contextmanager
def db_session(db_path: Optional[Path] = None) -> Iterator[sqlite3.Connection]:
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    preferred_language TEXT NOT NULL DEFAULT 'en',
    consent_accepted INTEGER NOT NULL DEFAULT 0,
    consent_accepted_at TEXT,
    retention_days INTEGER NOT NULL DEFAULT 30,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS medical_documents (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    page_count INTEGER NOT NULL DEFAULT 1,
    report_date TEXT,
    ocr_engine TEXT NOT NULL,
    ocr_quality_score REAL NOT NULL DEFAULT 0.0,
    ocr_quality_status TEXT NOT NULL DEFAULT 'good',
    ocr_warnings_json TEXT NOT NULL DEFAULT '[]',
    raw_ocr_text TEXT NOT NULL DEFAULT '',
    pages_json TEXT NOT NULL DEFAULT '[]',
    expires_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS document_classifications (
    id TEXT PRIMARY KEY,
    document_id TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL,
    predicted_type TEXT NOT NULL,
    final_type TEXT NOT NULL,
    confidence REAL NOT NULL,
    is_manual_override INTEGER NOT NULL DEFAULT 0,
    signals_json TEXT NOT NULL DEFAULT '[]',
    candidate_scores_json TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES medical_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS extracted_entities (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    name TEXT NOT NULL,
    value TEXT,
    unit TEXT,
    reference_range TEXT,
    date_value TEXT,
    dosage TEXT,
    frequency TEXT,
    duration TEXT,
    observation TEXT,
    source_page INTEGER NOT NULL DEFAULT 1,
    source_snippet TEXT NOT NULL DEFAULT '',
    confidence REAL NOT NULL DEFAULT 0.8,
    needs_verification INTEGER NOT NULL DEFAULT 0,
    verification_reason TEXT,
    verified_by_user INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES medical_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS laboratory_findings (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    test_name TEXT NOT NULL,
    canonical_test_key TEXT NOT NULL,
    value_numeric REAL,
    value_raw TEXT NOT NULL,
    unit TEXT,
    canonical_unit TEXT,
    ref_low REAL,
    ref_high REAL,
    ref_text TEXT,
    status TEXT NOT NULL,
    deviation_pct REAL,
    source_page INTEGER NOT NULL DEFAULT 1,
    source_snippet TEXT NOT NULL DEFAULT '',
    confidence REAL NOT NULL DEFAULT 0.8,
    needs_verification INTEGER NOT NULL DEFAULT 0,
    verification_reason TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES medical_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report_comparisons (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    doc_a_id TEXT NOT NULL,
    doc_b_id TEXT NOT NULL,
    matched_count INTEGER NOT NULL DEFAULT 0,
    incompatible_count INTEGER NOT NULL DEFAULT 0,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (doc_a_id) REFERENCES medical_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (doc_b_id) REFERENCES medical_documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS analysis_history (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    language TEXT NOT NULL DEFAULT 'en',
    ai_provider TEXT NOT NULL,
    summary_json TEXT NOT NULL,
    disclaimer TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES medical_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS qa_messages (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    citations_json TEXT NOT NULL DEFAULT '[]',
    information_unavailable INTEGER NOT NULL DEFAULT 0,
    language TEXT NOT NULL DEFAULT 'en',
    created_at TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES medical_documents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_docs_user ON medical_documents(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_entities_doc ON extracted_entities(document_id, user_id);
CREATE INDEX IF NOT EXISTS idx_labs_doc ON laboratory_findings(document_id, user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_doc ON analysis_history(document_id, user_id, language);
CREATE INDEX IF NOT EXISTS idx_qa_doc ON qa_messages(document_id, user_id);
"""


def init_db(db_path: Optional[Path] = None) -> None:
    with db_session(db_path) as conn:
        conn.executescript(SCHEMA_SQL)


def cleanup_expired_documents(db_path: Optional[Path] = None) -> int:
    now_iso = utc_now_iso()
    deleted = 0
    with db_session(db_path) as conn:
        rows = conn.execute(
            "SELECT id, stored_path FROM medical_documents WHERE expires_at IS NOT NULL AND expires_at <= ?",
            (now_iso,),
        ).fetchall()
        for row in rows:
            p = Path(row["stored_path"])
            if p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass
            conn.execute("DELETE FROM medical_documents WHERE id = ?", (row["id"],))
            deleted += 1
    return deleted


def parse_json_field(raw: Optional[str], default):
    if not raw:
        return default
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default
