from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# 🟡 Oracle 1: Validate incoming sensor data
@app.route("/ingest", methods=["POST"])
def ingest():
    data = request.get_json()
    panel_id = data.get("panelId")
    temperature = data.get("temperature")
    timestamp = data.get("timestamp")

    # 🔍 Basic validation
    if not panel_id or temperature is None:
        return jsonify({"error": "Missing data"}), 400
    if not (0 <= temperature <= 100):
        return jsonify({"error": "Temperature out of range"}), 422

    # ✅ Forward to ML
    print(f"[Oracle 1] ✅ Validated panel: {panel_id}, temp: {temperature}")
    return jsonify({"status": "ok", "forwardTo": "/ml/predict", "panelId": panel_id, "temperature": temperature})

# 🧠 Simulated ML logic
@app.route("/ml/predict", methods=["POST"])
def ml_predict():
    data = request.get_json()
    temperature = data.get("temperature")

    if temperature > 45:
        result = {"fault": "overheat", "confidence": 0.93}
    else:
        result = {"fault": "ok", "confidence": 0.99}

    print(f"[ML] 🔍 Prediction: {result}")
    return jsonify(result)

# 🟢 Oracle 2: Final validation + blockchain log
@app.route("/finalize", methods=["POST"])
def finalize():
    data = request.get_json()
    fault = data.get("fault")
    confidence = data.get("confidence")
    panel_id = data.get("panelId")

    if confidence >= 0.8 and fault != "ok":
        print(f"[Oracle 2] 🔗 Blockchain log: {panel_id}, FAULT: {fault}")
        return jsonify({"status": "logged", "fault": fault})
    else:
        return jsonify({"status": "not_logged", "reason": "low_confidence_or_no_fault"})

@app.route("/", methods=["GET"])
def home():
    return "ESP32 façade backend is running."

if __name__ == "__main__":
    app.run(debug=True)
