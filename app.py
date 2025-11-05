from flask import Flask, request, jsonify
from oracle1_validation import validate_payload
from ml_model import predict_fault, reload_model
from oracle2_finalize import finalize_event
import joblib
import os
import numpy as np
from sklearn.linear_model import LogisticRegression

app = Flask(__name__)

MODEL_PATH = "fault_model.pkl"

@app.route("/", methods=["GET"])
def health():
    return jsonify({"ok": True, "status": "Oracle backend running"})

@app.route("/ingest", methods=["POST"])
def ingest():
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"ok": False, "error": "Invalid JSON"}), 400

    # Oracle 1: validate payload
    valid, cleaned = validate_payload(data)
    if not valid:
        return jsonify({"ok": False, "error": cleaned.get("reason", "Validation failed")}), 400

    # ML: predict fault
    ml_ok, result = predict_fault(cleaned)
    if not ml_ok:
        return jsonify({"ok": False, "error": result.get("error", "ML model error")}), 500

    # Oracle 2: finalize event
    final_ok, status = finalize_event(cleaned.get("panel_id", "unknown"), result)
    if final_ok:
        return jsonify({"ok": True, "status": status}), 200
    else:
        return jsonify({"ok": False, "status": status}), 500

@app.route("/retrain", methods=["POST"])
def retrain():
    """
    Accepts JSON payload:
    {
        "features": [[25, 40, 0], [70, 90, 10], ...],   # List of feature lists
        "labels": [0, 1, ...]                           # List of int (0 or 1)
    }
    """
    try:
        data = request.get_json(force=True)
        X = np.array(data["features"])
        y = np.array(data["labels"])
        model = LogisticRegression()
        model.fit(X, y)
        joblib.dump(model, MODEL_PATH)
        reload_model()  # To reload the updated model in memory for immediate use
        return jsonify({"ok": True, "status": "Model trained and saved!"})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
