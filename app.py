from flask import Flask, request, jsonify, send_file, abort
from oracle1_validation import validate_payload
from ml_model import predict_fault, retrain_model
from oracle2_finalize import finalize_event

from web3 import Web3
import os, time

app = Flask(__name__)

panel_history = {}
ADMIN_API_KEY = "Admin_acsess_to_platform"

COLOR_CODES = {
    "not_installed":   ("Not installed yet", "gray"),
    "normal":          ("Installed and healthy (Normal operation)", "blue"),
    "warning":         ("Warning (abnormal values detected)", "yellow"),
    "fault":           ("Confirmed fault (urgent action needed)", "red"),
    "system_error":    ("Sensor/ML system/platform error (System error)", "purple"),
}

# --- Web3 setup ---
INFURA_URL = os.environ.get("INFURA_URL", "https://sepolia.infura.io/v3/51bc36040f314e85bf103ff18c570993")
w3 = Web3(Web3.HTTPProvider(INFURA_URL))

# ABI (paste your ABI JSON here)
abi = [
    {
        "inputs": [
            {"internalType": "string","name": "panel_id","type": "string"},
            {"internalType": "bool","name": "ok","type": "bool"},
            {"internalType": "string","name": "color","type": "string"},
            {"internalType": "string","name": "status","type": "string"},
            {"internalType": "int256","name": "prediction","type": "int256"},
            {"internalType": "string","name": "reason","type": "string"},
            {"internalType": "uint256","name": "timestamp","type": "uint256"}
        ],
        "name": "addPanelEvent",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

contract_address = "0xB0561d4580126DdF8DEEA9B7e356ee3F26A52e40"
contract = w3.eth.contract(address=contract_address, abi=abi)

oracle_private_key = os.environ["ORACLE_PRIVATE_KEY"]
oracle_account = w3.eth.account.from_key(oracle_private_key)

def log_to_blockchain(panel_id, backend_json):
    tx = contract.functions.addPanelEvent(
        panel_id,
        backend_json.get("ok", False),
        backend_json.get("color", "purple"),
        backend_json.get("status", "System error"),
        int(backend_json.get("prediction", -1)),
        backend_json.get("reason", ""),
        int(time.time())
    ).build_transaction({
        "from": oracle_account.address,
        "nonce": w3.eth.get_transaction_count(oracle_account.address),
        "gas": 500000,
        "gasPrice": w3.to_wei("10", "gwei")
    })

    signed_tx = w3.eth.account.sign_transaction(tx, oracle_private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return w3.to_hex(tx_hash)

# --- Flask routes ---

@app.route("/", methods=["GET"])
def health():
    return jsonify({"ok": True, "status": "Oracle backend running"})

@app.route('/download_model', methods=['GET'])
def download_model():
    api_key = request.headers.get("X-API-KEY")
    if api_key != ADMIN_API_KEY:
        abort(403)
    return send_file('fault_model.pkl', as_attachment=True)

@app.route("/ingest", methods=["POST"])
def ingest():
    try:
        data = request.get_json(force=True)
    except Exception:
        response = {
            "ok": False,
            "color": COLOR_CODES['system_error'][1],
            "status": COLOR_CODES['system_error'][0],
            "reason": "PlatformError",
            "prediction": -1
        }
        tx_hash = log_to_blockchain("unknown", response)
        response["tx_hash"] = tx_hash
        return jsonify(response), 400

    panel_id = data.get("panel_id", "unknown")

    if panel_id == "unknown" or not data:
        response = {
            "ok": False,
            "color": COLOR_CODES['not_installed'][1],
            "status": COLOR_CODES['not_installed'][0],
            "prediction": -1
        }
        tx_hash = log_to_blockchain(panel_id, response)
        response["tx_hash"] = tx_hash
        return jsonify(response), 200

    valid, cleaned = validate_payload(data)
    if not valid:
        reason = cleaned.get("reason", "Validation failed")
        error_type = "SensorError" if "sensor" in reason.lower() or "missing" in reason.lower() else "PlatformError"
        response = {
            "ok": False,
            "color": COLOR_CODES['system_error'][1],
            "status": COLOR_CODES['system_error'][0],
            "reason": error_type,
            "prediction": -1
        }
        tx_hash = log_to_blockchain(panel_id, response)
        response["tx_hash"] = tx_hash
        return jsonify(response), 400

    ml_ok, result = predict_fault(cleaned)
    if not ml_ok:
        response = {
            "ok": False,
            "color": COLOR_CODES['system_error'][1],
            "status": COLOR_CODES['system_error'][0],
            "reason": "MLFailure",
            "prediction": -1
        }
        tx_hash = log_to_blockchain(panel_id, response)
        response["tx_hash"] = tx_hash
        return jsonify(response), 500

    pred = result.get("prediction")
    color, status = COLOR_CODES['normal'][1], COLOR_CODES['normal'][0]
    cause = None

    if pred == 2 or pred == 1:
        color = COLOR_CODES['warning'][1] if pred == 2 else COLOR_CODES['fault'][1]
        status = COLOR_CODES['warning'][0] if pred == 2 else COLOR_CODES['fault'][0]
        st, at, x, y, z = cleaned['surface_temp'], cleaned['ambient_temp'], cleaned['accel_x'], cleaned['accel_y'], cleaned['accel_z']
        deviations = {
            "surface_temp": abs(st - 23.5),
            "ambient_temp": abs(at - 24.2),
            "accel_x": abs(x - 1.03),
            "accel_y": abs(y - 0.00),
            "accel_z": abs(z - -0.08)
        }
        main_sensor = max(deviations, key=deviations.get)
        if main_sensor == "surface_temp":
            cause = "Surface temperature abnormal"
        elif main_sensor == "ambient_temp":
            cause = "Ambient temperature abnormal"
        elif main_sensor.startswith("accel"):
            cause = "Orientation/tilt abnormal"
        else:
            cause = "Unknown anomaly"

    response = {
        "ok": True,
        "color": color,
        "status": status,
        "prediction": pred
    }
    if cause:
        response["reason"] = cause

    tx_hash = log_to_blockchain(panel_id, response)
    response["tx_hash"] = tx_hash

    return jsonify(response), 200

@app.route("/panel_history/<panel_id>", methods=["GET"])
def get_panel_history(panel_id):
    return jsonify({"panel_id": panel_id, "history": panel_history.get(panel_id, [])})

@app.route("/retrain", methods=["POST"])
def retrain():
    payload = request.get_json(force=True)
    features = payload.get("features")
    labels = payload.get("labels")
    if not features or not labels:
        return jsonify({"ok": False, "error": "Features and labels required"}), 400
    ok, msg = retrain_model(features, labels)
    if ok:
        return jsonify({"ok": True, "status": msg}), 200
    else:
        return jsonify({"ok": False, "error": msg}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
