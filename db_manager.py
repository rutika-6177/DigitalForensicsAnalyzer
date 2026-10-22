
"""
Forensic Evidence Database Manager
Handles SQLite storage, schema creation, deduplication queries, and record retrieval.
"""

import os
import sqlite3
from typing import List, Dict, Optional, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Vercel's application directory is read-only.
if os.environ.get("VERCEL"):
    DB_DIR = "/tmp/database"
    STORAGE_DIR = "/tmp/storage/images"
else:
    DB_DIR = os.path.join(PROJECT_ROOT, "database")
    STORAGE_DIR = os.path.join(PROJECT_ROOT, "storage", "images")

DB_PATH = os.path.join(DB_DIR, "forensic.db")


def init_db():
    """Ensure directories and database schema exist."""
    os.makedirs(DB_DIR, exist_ok=True)
    os.makedirs(STORAGE_DIR, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS evidence (
                id TEXT PRIMARY KEY,
                file_name TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                mime_type TEXT,
                dimensions TEXT,
                aspect_ratio TEXT,
                sha256 TEXT NOT NULL,
                md5 TEXT NOT NULL,
                dhash_hex TEXT NOT NULL,
                dhash_bin TEXT NOT NULL,
                status TEXT NOT NULL,
                match_type TEXT,
                matched_parent_id TEXT,
                similarity_score INTEGER,
                storage_path TEXT NOT NULL,
                is_physical_copy INTEGER NOT NULL DEFAULT 1,
                timestamp TEXT NOT NULL,
                device TEXT,
                custody_status TEXT
            )
        """)


def get_next_evidence_id() -> str:
    """Generate sequential evidence ID (e.g., EVD-001, EVD-002)."""
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT id FROM evidence ORDER BY rowid DESC LIMIT 1"
        ).fetchone()

    if not row:
        return "EVD-001"

    try:
        last_num = int(row[0].split("-")[1])
        return f"EVD-{last_num + 1:03d}"
    except (IndexError, ValueError):
        return f"EVD-{os.urandom(2).hex().upper()}"


def find_by_sha256(sha256: str) -> Optional[Dict]:
    """Find existing evidence by exact SHA-256 hash."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM evidence WHERE sha256 = ? "
            "ORDER BY rowid ASC LIMIT 1",
            (sha256,)
        ).fetchone()

    return dict(row) if row else None


def get_all_evidence() -> List[Dict]:
    """Retrieve all evidence records ordered by creation."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM evidence ORDER BY rowid ASC"
        ).fetchall()

    return [dict(row) for row in rows]


def insert_evidence(record: Dict) -> bool:
    """Insert a new evidence record into the database."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO evidence (
                id, file_name, file_size, mime_type, dimensions, aspect_ratio,
                sha256, md5, dhash_hex, dhash_bin, status, match_type,
                matched_parent_id, similarity_score, storage_path,
                is_physical_copy, timestamp, device, custody_status
            ) VALUES (
                :id, :file_name, :file_size, :mime_type, :dimensions,
                :aspect_ratio, :sha256, :md5, :dhash_hex, :dhash_bin,
                :status, :match_type, :matched_parent_id, :similarity_score,
                :storage_path, :is_physical_copy, :timestamp, :device,
                :custody_status
            )
        """, record)

    return True


def delete_evidence(evidence_id: str) -> Tuple[bool, Optional[str]]:
    """
    Delete evidence by ID.
    Returns (success, physical_file_to_delete_if_no_longer_referenced).
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        target = cursor.execute(
            "SELECT storage_path FROM evidence WHERE id = ?",
            (evidence_id,)
        ).fetchone()

        if not target:
            return False, None

        storage_path = target["storage_path"]

        cursor.execute("DELETE FROM evidence WHERE id = ?", (evidence_id,))

        ref_count = cursor.execute(
            "SELECT COUNT(*) FROM evidence WHERE storage_path = ?",
            (storage_path,)
        ).fetchone()[0]

    file_to_remove = None
    if ref_count == 0 and os.path.exists(storage_path):
        file_to_remove = storage_path

    return True, file_to_remove


def clear_all_evidence() -> bool:
    """Delete all evidence records and remove stored images."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM evidence")

    if os.path.exists(STORAGE_DIR):
        for filename in os.listdir(STORAGE_DIR):
            file_path = os.path.join(STORAGE_DIR, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except OSError:
                pass

    return True
