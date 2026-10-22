
import os
import sys
from flask import Flask, request, jsonify, send_from_directory

# -------------------- PROJECT PATHS --------------------

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = CURRENT_DIR

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from dsa_engine import DSAEngine
from seed_samples import generate_sample_image

UI_DIR = os.path.join(PROJECT_ROOT, "ui")

# Vercel's deployed project directory is read-only.
# Use /tmp for temporary files on Vercel.
if os.environ.get("VERCEL"):
    STORAGE_DIR = "/tmp/storage/images"
else:
    STORAGE_DIR = os.path.join(PROJECT_ROOT, "storage", "images")

os.makedirs(STORAGE_DIR, exist_ok=True)

app = Flask(__name__, static_folder=UI_DIR)
dsa_engine = DSAEngine()


# -------------------- FRONTEND --------------------

@app.route("/")
def index():
    return send_from_directory(UI_DIR, "index.html")


@app.route("/<path:path>")
def serve_ui(path):
    file_path = os.path.join(UI_DIR, path)

    if os.path.isfile(file_path):
        return send_from_directory(UI_DIR, path)

    return jsonify({"error": "Not found"}), 404


# -------------------- IMAGE STORAGE --------------------

@app.route("/storage/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(STORAGE_DIR, filename)


# -------------------- API --------------------

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "message": "Digital Forensics Analyzer API is running"
    })


@app.route("/api/evidence", methods=["GET"])
def get_evidence():
    try:
        evidence = dsa_engine.get_all_evidence()
        return jsonify(evidence)
    except Exception as e:
        app.logger.exception("Failed to retrieve evidence")
        return jsonify({"error": str(e)}), 500


@app.route("/api/upload", methods=["POST"])
def upload_evidence():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]

        if not file.filename:
            return jsonify({"error": "No file selected"}), 400

        os.makedirs(STORAGE_DIR, exist_ok=True)
        result = dsa_engine.add_evidence(file)

        return jsonify(result), 201

    except Exception as e:
        app.logger.exception("Failed to upload evidence")
        return jsonify({"error": str(e)}), 500


@app.route("/api/evidence/<evidence_id>", methods=["DELETE"])
def delete_evidence(evidence_id):
    try:
        result = dsa_engine.delete_evidence(evidence_id)
        return jsonify(result)
    except Exception as e:
        app.logger.exception("Failed to delete evidence")
        return jsonify({"error": str(e)}), 500


@app.route("/api/clear", methods=["POST"])
def clear_evidence():
    try:
        result = dsa_engine.clear_all()
        return jsonify(result)
    except Exception as e:
        app.logger.exception("Failed to clear evidence")
        return jsonify({"error": str(e)}), 500


@app.route("/api/sample", methods=["POST"])
def generate_sample():
    try:
        result = generate_sample_image()
        return jsonify(result), 201
    except Exception as e:
        app.logger.exception("Failed to generate sample")
        return jsonify({"error": str(e)}), 500


# -------------------- LOCAL DEVELOPMENT --------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        debug=False
    )
