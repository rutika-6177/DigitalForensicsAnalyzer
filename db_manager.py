"""
Forensic Evidence Database Manager
Handles SQLite persistent storage, schema creation, deduplication queries, and record retrieval.
"""

import os
import sqlite3
from typing import List, Dict, Optional, Tuple

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database')
DB_PATH = os.path.join(DB_DIR, 'forensic.db')
STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'storage', 'images')

def init_db():
    """Ensure database directory, storage directory, and table schema exist."""
    os.makedirs(DB_DIR, exist_ok=True)
    os.makedirs(STORAGE_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
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
    conn.commit()
    conn.close()

def get_next_evidence_id() -> str:
    """Generate sequential evidence ID (e.g., EVD-001, EVD-002)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM evidence ORDER BY rowid DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    if not row:
        return "EVD-001"
    try:
        last_num = int(row[0].split("-")[1])
        return f"EVD-{last_num + 1:03d}"
    except (IndexError, ValueError):
        return f"EVD-{os.urandom(2).hex().upper()}"

def find_by_sha256(sha256: str) -> Optional[Dict]:
    """Find existing evidence by exact SHA-256 hash."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM evidence WHERE sha256 = ? ORDER BY rowid ASC LIMIT 1", (sha256,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_evidence() -> List[Dict]:
    """Retrieve all evidence records ordered by creation."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM evidence ORDER BY rowid ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def insert_evidence(record: Dict) -> bool:
    """Insert a new evidence record into the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO evidence (
            id, file_name, file_size, mime_type, dimensions, aspect_ratio,
            sha256, md5, dhash_hex, dhash_bin, status, match_type,
            matched_parent_id, similarity_score, storage_path,
            is_physical_copy, timestamp, device, custody_status
        ) VALUES (
            :id, :file_name, :file_size, :mime_type, :dimensions, :aspect_ratio,
            :sha256, :md5, :dhash_hex, :dhash_bin, :status, :match_type,
            :matched_parent_id, :similarity_score, :storage_path,
            :is_physical_copy, :timestamp, :device, :custody_status
        )
    """, record)
    conn.commit()
    conn.close()
    return True

def delete_evidence(evidence_id: str) -> Tuple[bool, Optional[str]]:
    """
    Delete evidence by ID.
    Returns (success, physical_file_to_delete_if_no_longer_referenced).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT storage_path, is_physical_copy FROM evidence WHERE id = ?", (evidence_id,))
    target = cursor.fetchone()
    if not target:
        conn.close()
        return False, None

    storage_path = target["storage_path"]
    cursor.execute("DELETE FROM evidence WHERE id = ?", (evidence_id,))
    conn.commit()

    # Check if any remaining evidence records use this storage_path
    cursor.execute("SELECT COUNT(*) FROM evidence WHERE storage_path = ?", (storage_path,))
    ref_count = cursor.fetchone()[0]
    conn.close()

    file_to_remove = None
    if ref_count == 0 and os.path.exists(storage_path):
        file_to_remove = storage_path

    return True, file_to_remove

def clear_all_evidence() -> bool:
    """Wipe all evidence records from database and remove all physical images."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM evidence")
    conn.commit()
    conn.close()

    if os.path.exists(STORAGE_DIR):
        for f in os.listdir(STORAGE_DIR):
            file_path = os.path.join(STORAGE_DIR, f)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception:
                pass
    return True

