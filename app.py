from flask import Flask, request, jsonify
import time
from oracle1_validation import validate_payload
from ml_model import predict_fault
from oracle2_finalize import finalize_event

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health():
    return jsonify({"ok": True, "status": "Oracle backend running"})

@app.route("/ingest", methods=["POST"])
def ingest():
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"ok": False, "error": "Invalid JSON"}), 400

    valid, cleaned = validate_payload(data)
    if not valid:
        result = {"error": cleaned.get("reason", "Validation failed")}
    else:
        ml_ok, result = predict_fault(cleaned)
        if not ml_ok:
            result = {"error": result.get("error", "ML model error")}

    final_ok, status = finalize_event(cleaned.get("panel_id", "unknown"), result)
    if final_ok:
        return jsonify({"ok": True, "status": status}), 200
    else:
        return jsonify({"ok": False, "status": status}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
