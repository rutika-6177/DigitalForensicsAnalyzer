
"""
Forensic DSA Pipeline Engine
Maintains in-memory Data Structures (HashTable, EvidenceTree, EvidenceGraph)
and synchronizes with SQLite persistent storage and deduplicated file storage.
"""

import os
from datetime import datetime
from typing import Dict, Any

from hash_table import HashTable
from tree import EvidenceTree
from graph import EvidenceGraph
import db_manager
import hash_utils


class DSAEngine:
    def __init__(self):
        self.hash_table = HashTable(size=17)
        self.tree = EvidenceTree()
        self.graph = EvidenceGraph()
        self.reload_from_db()

    def reload_from_db(self):
        """Rebuild in-memory data structures from SQLite."""
        db_manager.init_db()
        self.hash_table = HashTable(size=17)
        self.tree = EvidenceTree()
        self.graph = EvidenceGraph()

        records = db_manager.get_all_evidence()

        for r in records:
            ev_id = r["id"]
            sha = r["sha256"]
            status = r["status"]
            parent_id = r["matched_parent_id"]

            if not self.hash_table.search(sha):
                self.hash_table.insert(sha, r)

            if status == "ORIGINAL" or not parent_id:
                self.tree.add_evidence(ev_id, r, parent_id="ROOT")
            else:
                self.tree.add_evidence(ev_id, r, parent_id=parent_id)

            self.graph.add_vertex(ev_id)

            if status == "DUPLICATE" and parent_id:
                weight = (
                    1.0 if r.get("match_type") == "EXACT_HASH"
                    else r.get("similarity_score", 90) / 100.0
                )
                self.graph.add_edge(
                    parent_id,
                    ev_id,
                    weight=weight,
                    relation_type=r.get("match_type", "DUPLICATE")
                )

    def get_all_evidence(self):
        """Return all evidence records from the database."""
        return db_manager.get_all_evidence()

    def process_and_store_image(
        self,
        file_name: str,
        file_bytes: bytes,
        mime_type: str = "image/jpeg"
    ) -> Dict[str, Any]:
        """Analyze an image, detect duplicates, store it, and index its evidence."""

        db_manager.init_db()

        # Ensure the image storage directory exists.
        os.makedirs(db_manager.STORAGE_DIR, exist_ok=True)

        sha256, md5 = hash_utils.compute_hashes(file_bytes)
        dhash_hex, dhash_bin, meta = hash_utils.compute_dhash(file_bytes)

        evidence_id = db_manager.get_next_evidence_id()
        file_size = len(file_bytes)
        timestamp = datetime.now().isoformat()

        exact_match = db_manager.find_by_sha256(sha256)

        status = "ORIGINAL"
        match_type = "NONE"
        similarity_score = 100
        matched_parent_id = None
        storage_path = ""
        is_physical_copy = 1

        if exact_match:
            status = "DUPLICATE"
            match_type = "EXACT_HASH"
            matched_parent_id = exact_match["id"]
            storage_path = exact_match["storage_path"]
            is_physical_copy = 0

        else:
            all_records = db_manager.get_all_evidence()
            lowest_dist = 64
            closest_rec = None

            for rec in all_records:
                dist = hash_utils.hamming_distance(
                    dhash_bin, rec["dhash_bin"]
                )
                if dist < lowest_dist:
                    lowest_dist = dist
                    closest_rec = rec

            if lowest_dist <= 6 and closest_rec:
                status = "DUPLICATE"
                match_type = "PERCEPTUAL_DHASH"
                similarity_score = hash_utils.calculate_similarity(
                    lowest_dist
                )
                matched_parent_id = closest_rec["id"]

                if (
                    similarity_score >= 96
                    and os.path.exists(closest_rec["storage_path"])
                ):
                    storage_path = closest_rec["storage_path"]
                    is_physical_copy = 0
                else:
                    ext = os.path.splitext(file_name)[1] or ".jpg"
                    unique_name = f"{evidence_id}_{sha256[:10]}{ext}"
                    storage_path = os.path.join(
                        db_manager.STORAGE_DIR, unique_name
                    )

                    with open(storage_path, "wb") as f:
                        f.write(file_bytes)

            else:
                ext = os.path.splitext(file_name)[1] or ".jpg"
                unique_name = f"{evidence_id}_{sha256[:10]}{ext}"
                storage_path = os.path.join(
                    db_manager.STORAGE_DIR, unique_name
                )

                with open(storage_path, "wb") as f:
                    f.write(file_bytes)

        record = {
            "id": evidence_id,
            "file_name": file_name,
            "file_size": file_size,
            "mime_type": mime_type,
            "dimensions": meta["dimensions"],
            "aspect_ratio": meta["aspect_ratio"],
            "sha256": sha256,
            "md5": md5,
            "dhash_hex": dhash_hex,
            "dhash_bin": dhash_bin,
            "status": status,
            "match_type": match_type,
            "matched_parent_id": matched_parent_id,
            "similarity_score": similarity_score,
            "storage_path": storage_path,
            "is_physical_copy": is_physical_copy,
            "timestamp": timestamp,
            "device": meta["device"],
            "custody_status": "Verified & Logged"
        }

        # Write a new physical copy only when required.
        if is_physical_copy:
            # The file may already have been written above.
            if not os.path.exists(storage_path):
                with open(storage_path, "wb") as f:
                    f.write(file_bytes)

        db_manager.insert_evidence(record)

        if not self.hash_table.search(sha256):
            self.hash_table.insert(sha256, record)

        self.tree.add_evidence(
            evidence_id,
            record,
            parent_id=matched_parent_id or "ROOT"
        )
        self.graph.add_vertex(evidence_id)

        if status == "DUPLICATE" and matched_parent_id:
            weight = (
                1.0 if match_type == "EXACT_HASH"
                else similarity_score / 100.0
            )
            self.graph.add_edge(
                matched_parent_id,
                evidence_id,
                weight=weight,
                relation_type=match_type
            )

        return record

    def delete_evidence(self, evidence_id: str) -> bool:
        """Delete evidence from the database and refresh data structures."""
        success, file_to_delete = db_manager.delete_evidence(evidence_id)

        if not success:
            return False

        if file_to_delete and os.path.exists(file_to_delete):
            try:
                os.remove(file_to_delete)
            except OSError:
                pass

        self.reload_from_db()
        return True

    def clear_all(self) -> bool:
        """Clear evidence records and refresh in-memory structures."""
        db_manager.clear_all_evidence()
        self.reload_from_db()
        return True

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Return evidence, counters, tree traversals, and graph edges."""
        records = self.get_all_evidence()

        total = len(records)
        originals = sum(1 for r in records if r["status"] == "ORIGINAL")
        duplicates = sum(1 for r in records if r["status"] == "DUPLICATE")
        exact_dups = sum(
            1 for r in records if r.get("match_type") == "EXACT_HASH"
        )
        near_dups = sum(
            1 for r in records if r.get("match_type") == "PERCEPTUAL_DHASH"
        )
        physical_files_count = sum(
            1 for r in records if r.get("is_physical_copy") == 1
        )

        edges = []
        for u, neighbor_list in self.graph.adj_list.items():
            for v, weight, rel in neighbor_list:
                if str(u) < str(v):
                    edges.append({
                        "source": u,
                        "target": v,
                        "weight": weight,
                        "relation_type": rel
                    })

        return {
            "evidence_list": records,
            "counters": {
                "total": total,
                "originals": originals,
                "duplicates": duplicates,
                "exact_duplicates": exact_dups,
                "near_duplicates": near_dups,
                "relationships": len(edges),
                "physical_files_count": physical_files_count
            },
            "tree": {
                "bfs": self.tree.bfs_traversal(),
                "preorder": self.tree.preorder_traversal()
            },
            "graph": {
                "edges": edges
            }
        }
