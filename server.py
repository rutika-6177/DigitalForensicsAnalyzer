"""
AegisForensics // Full-Stack Flask Backend & Server Launcher
Location: Forensic_Analyzer/server.py
Integrates Forensic DSA Engine, Persistent SQLite Database, Deduplication Storage, and Web UI.
"""

import os
import sys
import webbrowser
from flask import Flask, request, jsonify, send_from_directory

# Resolve directory paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dsa_engine import DSAEngine
from seed_samples import generate_sample_image

UI_DIR = os.path.join(PROJECT_ROOT, "ui")
STORAGE_DIR = os.path.join(PROJECT_ROOT, "storage", "images")
PORT = 8080

app = Flask(__name__, static_folder=UI_DIR)
dsa_engine = DSAEngine()

# =========================================================
# STATIC FILE & STORAGE IMAGE ROUTES
# =========================================================

@app.route("/")
def index():
    return send_from_directory(UI_DIR, "index.html")

@app.route("/<path:path>")
def static_files(path):
    if os.path.exists(os.path.join(UI_DIR, path)):
        return send_from_directory(UI_DIR, path)
    return ("File Not Found", 404)

@app.route("/storage/images/<path:filename>")
def serve_storage_image(filename):
    if os.path.exists(os.path.join(STORAGE_DIR, filename)):
        return send_from_directory(STORAGE_DIR, filename)
    return ("Image Not Found", 404)

# =========================================================
# REST API ENDPOINTS
# =========================================================

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "engine": "AegisForensics DSA Core",
        "database": "SQLite (database/forensic.db)",
        "storage": "storage/images/"
    })

@app.route("/api/evidence", methods=["GET"])
def get_evidence():
    """Retrieve all evidence records, counters, tree, and graph from persistent storage."""
    summary = dsa_engine.get_dashboard_summary()
    return jsonify(summary)

@app.route("/api/upload", methods=["POST"])
def upload_evidence():
    """
    Handle evidence image upload:
    - Calculates SHA-256, MD5, and dHash.
    - Exact duplicate: 0 new physical copies written.
    - Distinct original: unique physical file written to storage/images/.
    - Persists record in SQLite database.
    - Updates in-memory Tree and Graph.
    """
    if "files" not in request.files and "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    uploaded_files = request.files.getlist("files") or [request.files["file"]]
    processed_results = []

    for file in uploaded_files:
        if not file.filename:
            continue
        file_bytes = file.read()
        if not file_bytes:
            continue

        mime_type = file.content_type or "image/jpeg"
        record = dsa_engine.process_and_store_image(
            file_name=file.filename,
            file_bytes=file_bytes,
            mime_type=mime_type
        )
        processed_results.append(record)

    summary = dsa_engine.get_dashboard_summary()
    return jsonify({
        "success": True,
        "processed": processed_results,
        "summary": summary
    })

@app.route("/api/evidence/<evidence_id>", methods=["DELETE"])
def delete_evidence_item(evidence_id):
    """Delete evidence from DB and clean up physical file if not shared by duplicates."""
    success = dsa_engine.delete_evidence(evidence_id)
    if not success:
        return jsonify({"error": "Evidence not found"}), 404
    summary = dsa_engine.get_dashboard_summary()
    return jsonify({"success": True, "summary": summary})

@app.route("/api/clear", methods=["POST"])
def clear_all_evidence():
    """Wipe all evidence records from SQLite and purge all files from storage/images/."""
    dsa_engine.clear_all()
    summary = dsa_engine.get_dashboard_summary()
    return jsonify({"success": True, "summary": summary})

@app.route("/api/sample", methods=["POST"])
def load_sample_dataset():
    """Generate and store sample forensic dataset in persistent storage."""
    specimens = [
        ("crime_scene_alleyway_orig.jpg", generate_sample_image("CRIME SCENE #01: ALLEY", (15, 32, 39), (44, 83, 100))),
        ("crime_scene_alleyway_copy.jpg", None), # Will be exact duplicate bytes of above
        ("suspect_sedan_plate.jpg", generate_sample_image("SUSPECT VEHICLE: PLATE", (32, 1, 34), (111, 0, 0))),
        ("suspect_sedan_plate_crop.jpg", generate_sample_image("SUSPECT VEHICLE: PLATE", (32, 1, 34), (111, 0, 0), watermark=True))
    ]

    orig_bytes = specimens[0][1]
    results = []

    # 1. Specimen 1 (Original)
    r1 = dsa_engine.process_and_store_image("crime_scene_alleyway_orig.jpg", orig_bytes)
    results.append(r1)

    # 2. Specimen 2 (Exact Duplicate of 1 - Same bytes)
    r2 = dsa_engine.process_and_store_image("crime_scene_alleyway_copy.jpg", orig_bytes)
    results.append(r2)

    # 3. Specimen 3 (Another Original)
    r3 = dsa_engine.process_and_store_image("suspect_sedan_plate.jpg", specimens[2][1])
    results.append(r3)

    # 4. Specimen 4 (Perceptual Duplicate of 3)
    r4 = dsa_engine.process_and_store_image("suspect_sedan_plate_crop.jpg", specimens[3][1])
    results.append(r4)

    summary = dsa_engine.get_dashboard_summary()
    return jsonify({
        "success": True,
        "processed": results,
        "summary": summary
    })

def find_open_port(start_port=8080):
    import socket
    for p in range(start_port, start_port + 15):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("", p))
            s.close()
            return p
        except OSError:
            continue
    return start_port

def main():
    actual_port = find_open_port(PORT)
    print("=" * 65)
    print("  AEGIS FORENSICS // DIGITAL EVIDENCE & DUPLICATE ANALYZER")
    print(f"  Server online at: http://127.0.0.1:{actual_port}")
    print("  Database: database/forensic.db (SQLite Persistent Storage)")
    print("  Storage:  storage/images/ (Deduplicated Repository)")
    print("=" * 65)

    try:
        webbrowser.open(f"http://127.0.0.1:{actual_port}")
    except Exception:
        pass

    app.run(host="0.0.0.0", port=actual_port, debug=False)

if __name__ == "__main__":
    main()
