from flask import Flask, request, jsonify, send_file, abort
from oracle1_validation import validate_payload
from ml_model import predict_fault, retrain_model
from oracle2_finalize import finalize_event

app = Flask(__name__)

# In-memory store for per-panel records (cleared on restart)
panel_history = {}

# Set your admin API key here (change this for production!)
ADMIN_API_KEY = "Admin_acsess_to_platform"

def diagnose_fault(data):
    messages = []
    # Check surface temperature
    if data.get('surface_temp') is not None and (data['surface_temp'] < 20 or data['surface_temp'] > 35):
        messages.append("Surface temperature out of safe range")
    # Check ambient temperature
    if data.get('ambient_temp') is not None and (data['ambient_temp'] < 20 or data['ambient_temp'] > 35):
        messages.append("Ambient temperature out of safe range")
    # Check for abnormal orientation (tilt/fall)
    if (abs(data.get('accel_x', 0)) > 1.2 or
        abs(data.get('accel_y', 0)) > 1.2 or
        abs(data.get('accel_z', 1)) < 0.8):
        messages.append("Panel orientation abnormal (possible tilt or displacement)")
    if not messages:
        messages.append("Anomaly detected (unspecified)")
    return "; ".join(messages)

@app.route("/", methods=["GET"])
def health():
    return jsonify({"ok": True, "status": "Oracle backend running"})

@app.route('/download_model', methods=['GET'])
def download_model():
    api_key = request.headers.get("X-API-KEY")
    if api_key != ADMIN_API_KEY:
        abort(403)  # Forbidden
    return send_file('fault_model.pkl', as_attachment=True)

@app.route("/ingest", methods=["POST"])
def ingest():
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"ok": False, "error": "Invalid JSON"}), 400

    panel_id = data.get("panel_id", "unknown")

    # Oracle 1: validate payload
    valid, cleaned = validate_payload(data)
    if not valid:
        # Save fault to panel history
        panel_history.setdefault(panel_id, []).append({"input": data, "result": cleaned})
        return jsonify({"ok": False, "error": cleaned.get("reason", "Validation failed")}), 400

    # ML: predict fault
    ml_ok, result = predict_fault(cleaned)
    if not ml_ok:
        panel_history.setdefault(panel_id, []).append({"input": data, "result": result})
        return jsonify({"ok": False, "error": result.get("error", "ML model error")}), 500

    # Oracle 2: finalize event
    final_ok, status = finalize_event(panel_id, result)
    # Log every result per panel
    panel_history.setdefault(panel_id, []).append({"input": data, "result": status})

    if final_ok:
        # If status indicates a fault, add diagnosis
        if "Fault
