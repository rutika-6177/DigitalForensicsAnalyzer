
"""
Forensic DSA Pipeline Engine
Maintains HashTable, EvidenceTree, and EvidenceGraph.
Synchronizes evidence records with SQLite and image storage.
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

    def get_all_evidence(self):
        """Return all evidence records from the database."""
        db_manager.init_db()
        return db_manager.get_all_evidence()

    def reload_from_db(self):
        """Rebuild in-memory data structures from SQLite."""
        db_manager.init_db()

        self.hash_table = HashTable(size=17)
        self.tree = EvidenceTree()
        self.graph = EvidenceGraph()

        records = self.get_all_evidence()

        for record in records:
            ev_id = record["id"]
            sha = record["sha256"]
            status = record["status"]
            parent_id = record.get("matched_parent_id")

            if not self.hash_table.search(sha):
                self.hash_table.insert(sha, record)

            if status == "ORIGINAL" or not parent_id:
                self.tree.add_evidence(ev_id, record, parent_id="ROOT")
            else:
                self.tree.add_evidence(ev_id, record, parent_id=parent_id)

            self.graph.add_vertex(ev_id)

            if status == "DUPLICATE" and parent_id:
                similarity = record.get("similarity_score", 90)
                weight = (
                    1.0
                    if record.get("match_type") == "EXACT_HASH"
                    else float(similarity) / 100.0
                )
                self.graph.add_edge(
                    parent_id,
                    ev_id,
                    weight=weight,
                    relation_type=record.get("match_type", "DUPLICATE")
                )

    def process_and_store_image(
        self,
        file_name: str,
        file_bytes: bytes,
        mime_type: str = "image/jpeg"
    ) -> Dict[str, Any]:
        """Analyze an image, detect duplicates, store it, and index evidence."""

        if not file_bytes:
            raise ValueError("The uploaded file is empty.")

        db_manager.init_db()
        os.makedirs(db_manager.STORAGE_DIR, exist_ok=True)

        sha256, md5 = hash_utils.compute_hashes(file_bytes)
        dhash_hex, dhash_bin, meta = hash_utils.compute_dhash(file_bytes)

        evidence_id = db_manager.get_next_evidence_id()
        timestamp = datetime.now().isoformat()
        file_size = len(file_bytes)

        exact_match = db_manager.find_by_sha256(sha256)

        status = "ORIGINAL"
        match_type = "NONE"
        similarity_score = 100
        matched_parent_id = None
        storage_path = ""
        is_physical_copy = 1
        should_write_file = True

        if exact_match:
            # Exact duplicate: reuse the original file path.
            status = "DUPLICATE"
            match_type = "EXACT_HASH"
            matched_parent_id = exact_match["id"]
            storage_path = exact_match["storage_path"]
            is_physical_copy = 0
            should_write_file = False

        else:
            records = self.get_all_evidence()
            closest_record = None
            lowest_distance = 65

            for record in records:
                existing_hash = record.get("dhash_bin")
                if not existing_hash:
                    continue

                distance = hash_utils.hamming_distance(
                    dhash_bin, existing_hash
                )

                if distance < lowest_distance:
                    lowest_distance = distance
                    closest_record = record

            if closest_record and lowest_distance <= 6:
                status = "DUPLICATE"
                match_type = "PERCEPTUAL_DHASH"
                similarity_score = hash_utils.calculate_similarity(
                    lowest_distance
                )
                matched_parent_id = closest_record["id"]

                # Reuse the existing file only when the similarity is high
                # and the referenced file is actually available.
                existing_path = closest_record.get("storage_path", "")

                if (
                    similarity_score >= 96
                    and existing_path
                    and os.path.exists(existing_path)
                ):
                    storage_path = existing_path
                    is_physical_copy = 0
                    should_write_file = False

            if should_write_file:
                extension = os.path.splitext(file_name or "")[1].lower()

                # Avoid using arbitrary filenames as storage paths.
                if not extension or len(extension) > 10:
                    extension = ".jpg"

                unique_name = f"{evidence_id}_{sha256[:12]}{extension}"
                storage_path = os.path.join(
                    db_manager.STORAGE_DIR, unique_name
                )

                with open(storage_path, "wb") as image_file:
                    image_file.write(file_bytes)

        record = {
            "id": evidence_id,
            "file_name": os.path.basename(file_name or "upload.jpg"),
            "file_size": file_size,
            "mime_type": mime_type or "application/octet-stream",
            "dimensions": meta.get("dimensions"),
            "aspect_ratio": meta.get("aspect_ratio"),
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
            "device": meta.get("device"),
            "custody_status": "Verified & Logged"
        }

        try:
            db_manager.insert_evidence(record)
        except Exception:
            # Remove a newly written image if its database insert fails.
            if should_write_file and storage_path and os.path.exists(storage_path):
                try:
                    os.remove(storage_path)
                except OSError:
                    pass
            raise

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
                1.0
                if match_type == "EXACT_HASH"
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
        """Delete evidence and rebuild in-memory structures."""
        success, file_to_delete = db_manager.delete_evidence(evidence_id)

        if not success:
            return False

        # Delete the image only if no remaining record references it.
        if file_to_delete and os.path.exists(file_to_delete):
            remaining_records = self.get_all_evidence()
            still_referenced = any(
                r.get("storage_path") == file_to_delete
                for r in remaining_records
            )

            if not still_referenced:
                try:
                    os.remove(file_to_delete)
                except OSError:
                    pass

        self.reload_from_db()
        return True

    def clear_all(self) -> bool:
        """Clear evidence records and rebuild in-memory structures."""
        db_manager.clear_all_evidence()
        self.reload_from_db()
        return True

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Return evidence, counters, tree traversals, and graph edges."""
        records = self.get_all_evidence()

        total = len(records)
        originals = sum(
            1 for r in records if r.get("status") == "ORIGINAL"
        )
        duplicates = sum(
            1 for r in records if r.get("status") == "DUPLICATE"
        )
        exact_dups = sum(
            1 for r in records if r.get("match_type") == "EXACT_HASH"
        )
        near_dups = sum(
            1 for r in records
            if r.get("match_type") == "PERCEPTUAL_DHASH"
        )
        physical_files_count = sum(
            1 for r in records if r.get("is_physical_copy") == 1
        )

        edges = []
        seen_edges = set()

        for source, neighbors in self.graph.adj_list.items():
            for target, weight, relation in neighbors:
                edge_key = frozenset((str(source), str(target)))

                if edge_key in seen_edges:
                    continue

                seen_edges.add(edge_key)
                edges.append({
                    "source": source,
                    "target": target,
                    "weight": weight,
                    "relation_type": relation
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
