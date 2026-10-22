
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
        """Rebuild in-memory structures from stored evidence."""
        db_manager.init_db()

        self.hash_table = HashTable(size=17)
        self.tree = EvidenceTree()
        self.graph = EvidenceGraph()

        for record in self.get_all_evidence():
            evidence_id = record["id"]
            sha256 = record["sha256"]
            status = record.get("status", "ORIGINAL")
            parent_id = record.get("matched_parent_id")

            if not self.hash_table.search(sha256):
                self.hash_table.insert(sha256, record)

            tree_parent = (
                parent_id
                if status == "DUPLICATE" and parent_id
                else "ROOT"
            )
            self.tree.add_evidence(
                evidence_id, record, parent_id=tree_parent
            )

            self.graph.add_vertex(evidence_id)

            if status == "DUPLICATE" and parent_id:
                similarity = float(
                    record.get("similarity_score") or 90
                )
                weight = (
                    1.0
                    if record.get("match_type") == "EXACT_HASH"
                    else similarity / 100.0
                )
                self.graph.add_edge(
                    parent_id,
                    evidence_id,
                    weight=weight,
                    relation_type=record.get(
                        "match_type", "DUPLICATE"
                    )
                )

    def process_and_store_image(
        self,
        file_name: str,
        file_bytes: bytes,
        mime_type: str = "image/jpeg"
    ) -> Dict[str, Any]:
        """Analyze, deduplicate, store, and index an uploaded image."""

        if not file_bytes:
            raise ValueError("The uploaded file is empty.")

        db_manager.init_db()
        os.makedirs(db_manager.STORAGE_DIR, exist_ok=True)

        # Validate that the uploaded bytes can be processed as an image.
        try:
            sha256, md5 = hash_utils.compute_hashes(file_bytes)
            dhash_hex, dhash_bin, meta = hash_utils.compute_dhash(
                file_bytes
            )
        except Exception as exc:
            raise ValueError(
                "The uploaded file is not a supported or valid image."
            ) from exc

        if not isinstance(meta, dict):
            raise ValueError("Image metadata could not be read.")

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
        wrote_new_file = False

        if exact_match:
            # Identical bytes: reference the existing image.
            status = "DUPLICATE"
            match_type = "EXACT_HASH"
            matched_parent_id = exact_match["id"]
            storage_path = exact_match["storage_path"]
            is_physical_copy = 0

        else:
            closest_record = None
            lowest_distance = 65

            for existing in self.get_all_evidence():
                existing_dhash = existing.get("dhash_bin")
                if not existing_dhash:
                    continue

                distance = hash_utils.hamming_distance(
                    dhash_bin, existing_dhash
                )

                if distance < lowest_distance:
                    lowest_distance = distance
                    closest_record = existing

            if closest_record and lowest_distance <= 6:
                status = "DUPLICATE"
                match_type = "PERCEPTUAL_DHASH"
                similarity_score = hash_utils.calculate_similarity(
                    lowest_distance
                )
                matched_parent_id = closest_record["id"]

                existing_path = closest_record.get("storage_path", "")

                # Reuse the file only if it is available and similarity
                # is sufficiently high.
                if (
                    similarity_score >= 96
                    and existing_path
                    and os.path.isfile(existing_path)
                ):
                    storage_path = existing_path
                    is_physical_copy = 0

            # Originals and near-duplicates with no reusable file get
            # their own image file.
            if not storage_path:
                extension = os.path.splitext(
                    os.path.basename(file_name or "")
                )[1].lower()

                allowed_extensions = {
                    ".jpg", ".jpeg", ".png", ".gif",
                    ".webp", ".bmp", ".tif", ".tiff"
                }

                if extension not in allowed_extensions:
                    extension = ".jpg"

                unique_name = f"{evidence_id}_{sha256[:12]}{extension}"
                storage_path = os.path.join(
                    db_manager.STORAGE_DIR, unique_name
                )

                with open(storage_path, "wb") as image_file:
                    image_file.write(file_bytes)

                wrote_new_file = True

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

        # If the database insert fails, remove the newly created image.
        try:
            db_manager.insert_evidence(record)
        except Exception:
            if wrote_new_file and os.path.isfile(storage_path):
                try:
                    os.remove(storage_path)
                except OSError:
                    pass
            raise

        # Rebuild from the database to keep all structures consistent.
        self.reload_from_db()
        return record

    def delete_evidence(self, evidence_id: str) -> bool:
        """Delete a record and remove its image if no record uses it."""
        success, file_to_delete = db_manager.delete_evidence(evidence_id)

        if not success:
            return False

        if file_to_delete and os.path.isfile(file_to_delete):
            still_referenced = any(
                record.get("storage_path") == file_to_delete
                for record in self.get_all_evidence()
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
        """Return evidence records, counters, tree, and graph."""
        records = self.get_all_evidence()

        total = len(records)
        originals = sum(
            1 for r in records if r.get("status") == "ORIGINAL"
        )
        duplicates = sum(
            1 for r in records if r.get("status") == "DUPLICATE"
        )
        exact_duplicates = sum(
            1 for r in records if r.get("match_type") == "EXACT_HASH"
        )
        near_duplicates = sum(
            1 for r in records
            if r.get("match_type") == "PERCEPTUAL_DHASH"
        )
        physical_files = sum(
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
                "exact_duplicates": exact_duplicates,
                "near_duplicates": near_duplicates,
                "relationships": len(edges),
                "physical_files_count": physical_files
            },
            "tree": {
                "bfs": self.tree.bfs_traversal(),
                "preorder": self.tree.preorder_traversal()
            },
            "graph": {
                "edges": edges
            }
        }
