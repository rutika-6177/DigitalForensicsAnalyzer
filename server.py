
import os
import sys
from flask import Flask, request, jsonify, send_from_directory

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = CURRENT_DIR

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import db_manager
from dsa_engine import DSAEngine
from seed_samples import generate_sample_image

UI_DIR = os.path.join(PROJECT_ROOT, "ui")

if os.environ.get("VERCEL"):
    STORAGE_DIR = "/tmp/storage/images"
else:
    STORAGE_DIR = os.path.join(PROJECT_ROOT, "storage", "images")

os.makedirs(STORAGE_DIR, exist_ok=True)

app = Flask(__name__, static_folder=UI_DIR)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

dsa_engine = DSAEngine()


@app.route("/")
def index():
    return send_from_directory(UI_DIR, "index.html")


@app.route("/<path:path>")
def serve_ui(path):
    file_path = os.path.join(UI_DIR, path)

    if os.path.isfile(file_path):
        return send_from_directory(UI_DIR, path)

    return jsonify({"error": "Not found"}), 404


@app.route("/storage/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(STORAGE_DIR, filename)


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "Digital Forensics Analyzer API is running"
    }), 200


@app.route("/api/evidence", methods=["GET"])
def get_evidence():
    try:
        db_manager.init_db()
        records = db_manager.get_all_evidence()
        return jsonify(records), 200
    except Exception:
        app.logger.exception("Failed to retrieve evidence")
        return jsonify({"error": "Failed to retrieve evidence"}), 500


@app.route("/api/upload", methods=["POST"])
def upload_evidence():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    try:
        file_bytes = file.read()

        if not file_bytes:
            return jsonify({"error": "The uploaded file is empty"}), 400

        os.makedirs(STORAGE_DIR, exist_ok=True)

        result = dsa_engine.process_and_store_image(
            file_name=file.filename,
            file_bytes=file_bytes,
            mime_type=file.mimetype or "application/octet-stream"
        )

        return jsonify(result), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    except Exception:
        app.logger.exception("Failed to upload evidence")
        return jsonify({
            "error": "Upload failed. Check Vercel Runtime Logs."
        }), 500


@app.route("/api/evidence/<evidence_id>", methods=["DELETE"])
def delete_evidence(evidence_id):
    try:
        result = dsa_engine.delete_evidence(evidence_id)
        return jsonify(result), 200
    except Exception:
        app.logger.exception("Failed to delete evidence")
        return jsonify({"error": "Failed to delete evidence"}), 500


@app.route("/api/clear", methods=["POST"])
def clear_evidence():
    try:
        result = dsa_engine.clear_all()
        return jsonify(result), 200
    except Exception:
        app.logger.exception("Failed to clear evidence")
        return jsonify({"error": "Failed to clear evidence"}), 500


@app.route("/api/sample", methods=["POST"])
def generate_sample():
    try:
        result = generate_sample_image()
        return jsonify(result), 201
    except Exception:
        app.logger.exception("Failed to generate sample")
        return jsonify({"error": "Failed to generate sample image"}), 500


@app.errorhandler(413)
def file_too_large(error):
    return jsonify({
        "error": "File too large. Maximum upload size is 10 MB."
    }), 413


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        debug=False
    )
