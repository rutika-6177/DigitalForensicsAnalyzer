
import os
import sys
from flask import Flask, request, jsonify, send_from_directory

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = CURRENT_DIR

if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from dsa_engine import DSAEngine
from seed_samples import generate_sample_image

UI_DIR = os.path.join(PROJECT_ROOT, "ui")

if os.environ.get("VERCEL"):
    STORAGE_DIR = "/tmp/storage/images"
else:
    STORAGE_DIR = os.path.join(PROJECT_ROOT, "storage", "images")

os.makedirs(STORAGE_DIR, exist_ok=True)

app = Flask(__name__, static_folder=UI_DIR)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

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


# Return the response format expected by the frontend.
@app.route("/api/evidence", methods=["GET"])
def get_evidence():
    try:
        return jsonify(dsa_engine.get_dashboard_summary()), 200
    except Exception:
        app.logger.exception("Failed to retrieve evidence")
        return jsonify({
            "error": "Failed to retrieve evidence"
        }), 500


# Accept both "files" and "file" as upload field names.
@app.route("/api/upload", methods=["POST"])
def upload_evidence():
    uploaded_files = request.files.getlist("files")

    if not uploaded_files:
        uploaded_files = request.files.getlist("file")

    uploaded_files = [
        f for f in uploaded_files
        if f and f.filename
    ]

    if not uploaded_files:
        return jsonify({
            "error": "No files received. Please select an image."
        }), 400

    processed = []
    errors = []

    try:
        os.makedirs(STORAGE_DIR, exist_ok=True)

        for file in uploaded_files:
            file_bytes = file.read()

            if not file_bytes:
                errors.append(f"{file.filename}: empty file")
                continue

            try:
                record = dsa_engine.process_and_store_image(
                    file_name=file.filename,
                    file_bytes=file_bytes,
                    mime_type=(
                        file.mimetype or "application/octet-stream"
                    )
                )
                processed.append(record)

            except ValueError as e:
                errors.append(f"{file.filename}: {str(e)}")

        if not processed:
            return jsonify({
                "error": "No images were processed successfully.",
                "details": errors
            }), 400

        # The frontend expects both "summary" and "processed".
        return jsonify({
            "summary": dsa_engine.get_dashboard_summary(),
            "processed": processed,
            "errors": errors
        }), 201

    except Exception:
        app.logger.exception("Failed to upload evidence")
        return jsonify({
            "error": "Upload failed. Check Vercel Runtime Logs."
        }), 500


@app.route("/api/evidence/<evidence_id>", methods=["DELETE"])
def delete_evidence(evidence_id):
    try:
        success = dsa_engine.delete_evidence(evidence_id)

        if not success:
            return jsonify({
                "error": "Evidence ID not found"
            }), 404

        return jsonify({
            "success": True,
            "summary": dsa_engine.get_dashboard_summary()
        }), 200

    except Exception:
        app.logger.exception("Failed to delete evidence")
        return jsonify({
            "error": "Failed to delete evidence"
        }), 500


@app.route("/api/clear", methods=["POST"])
def clear_evidence():
    try:
        dsa_engine.clear_all()

        return jsonify({
            "success": True,
            "summary": dsa_engine.get_dashboard_summary()
        }), 200

    except Exception:
        app.logger.exception("Failed to clear evidence")
        return jsonify({
            "error": "Failed to clear evidence"
        }), 500


@app.route("/api/sample", methods=["POST"])
def generate_sample():
    try:
        # The sample generator returns image bytes, not JSON.
        image_bytes = generate_sample_image("SAMPLE EVIDENCE")

        record = dsa_engine.process_and_store_image(
            file_name="sample_evidence.jpg",
            file_bytes=image_bytes,
            mime_type="image/jpeg"
        )

        return jsonify({
            "summary": dsa_engine.get_dashboard_summary(),
            "processed": [record]
        }), 201

    except Exception:
        app.logger.exception("Failed to generate sample")
        return jsonify({
            "error": "Failed to generate sample image"
        }), 500


@app.errorhandler(413)
def file_too_large(error):
    return jsonify({
        "error": "Upload is too large. Maximum request size is 10 MB."
    }), 413


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        debug=False
    )
