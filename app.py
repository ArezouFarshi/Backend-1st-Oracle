from flask import Flask, request, jsonify
import time
from oracle1_validation import validate_payload
from ml_model import predict_fault
from oracle2_finalize import finalize_event

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health():
    return jsonify({"ok": True, "panel_id": "ID_27_C_42", "status": "Oracle backend running"})

@app.route("/ingest", methods=["POST"])
def ingest():
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"ok": False, "error": "Invalid JSON"}), 400

    valid, cleaned = validate_payload(data)
    if not valid:
        return jsonify({"ok": False, "error": "Sensor validation failed", "details": cleaned}), 406

    ml_ok, result = predict_fault(cleaned)
    if not ml_ok:
        return jsonify({"ok": False, "error": "ML model failed"}), 500

    final_ok, status = finalize_event(cleaned["panel_id"], result)
    if final_ok:
        return jsonify({"ok": True, "anchored": True, "status": status})
    else:
        return jsonify({"ok": False, "error": "Rejected by Oracle 2", "status": status}), 406

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
