"""
Digital Forensic and Evidence Analyzer // Python CLI Runner
Runs the Forensic DSA Engine, demonstrates duplicate detection,
and shows persistent storage & deduplication stats directly from the terminal.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
FORENSIC_DIR = os.path.dirname(os.path.abspath(__file__))
if FORENSIC_DIR not in sys.path:
    sys.path.insert(0, FORENSIC_DIR)

from dsa_engine import DSAEngine
from seed_samples import generate_sample_image

def run_cli_demonstration():
    print("=" * 65)
    print("  AEGIS FORENSICS // DATA STRUCTURE ANALYSIS & STORAGE ENGINE")
    print("=" * 65)

    engine = DSAEngine()

    # Create 3 specimen images
    img1_bytes = generate_sample_image("EVIDENCE A: CRIME SCENE", (15, 32, 39), (44, 83, 100))
    img2_bytes = img1_bytes # Exact duplicate bytes
    img3_bytes = generate_sample_image("EVIDENCE B: SUSPECT VEHICLE", (32, 1, 34), (111, 0, 0))

    print("\n--- 1. Uploading Specimen 1 (Original Photo) ---")
    r1 = engine.process_and_store_image("crime_scene_alley.jpg", img1_bytes)
    print(f"Result: {r1['id']} -> Status: {r1['status']}, Physical Copy Stored: {bool(r1['is_physical_copy'])}")
    print(f"Storage Path: {r1['storage_path']}")

    print("\n--- 2. Uploading Specimen 2 (Exact Duplicate of Specimen 1) ---")
    r2 = engine.process_and_store_image("crime_scene_alley_backup.jpg", img2_bytes)
    print(f"Result: {r2['id']} -> Status: {r2['status']}, Matched Parent: {r2['matched_parent_id']}")
    print(f"Deduplication: Physical Copy Stored: {bool(r2['is_physical_copy'])} (0 bytes written, reused {r1['id']} file)")
    print(f"Storage Path: {r2['storage_path']}")

    print("\n--- 3. Uploading Specimen 3 (Different Original Photo) ---")
    r3 = engine.process_and_store_image("suspect_vehicle.jpg", img3_bytes)
    print(f"Result: {r3['id']} -> Status: {r3['status']}, Physical Copy Stored: {bool(r3['is_physical_copy'])}")
    print(f"Storage Path: {r3['storage_path']}")

    # Summary
    summary = engine.get_dashboard_summary()
    counters = summary["counters"]
    print("\n" + "=" * 65)
    print("  PERSISTENT DASHBOARD METRICS (SQLite + Disk)")
    print("=" * 65)
    print(f"  * Total Images Logged:    {counters['total']}")
    print(f"  * Original Images:        {counters['originals']}")
    print(f"  * Duplicate Images:       {counters['duplicates']}")
    print(f"  * Physical Files on Disk: {counters['physical_files_count']} (Deduplicated!)")

    print("\n--- Tree Hierarchy Traversals ---")
    print("  * BFS (Level-Order):", " -> ".join(summary["tree"]["bfs"]))
    print("  * Pre-Order:        ", " -> ".join(summary["tree"]["preorder"]))

if __name__ == "__main__":
    run_cli_demonstration()