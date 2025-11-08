import joblib
import numpy as np
import os
from sklearn.linear_model import LogisticRegression

MODEL_PATH = "fault_model.pkl"

def is_model_available():
    return os.path.exists(MODEL_PATH)

def load_model():
    if is_model_available():
        return joblib.load(MODEL_PATH)
    return None

def predict_fault(data: dict):
    """
    Returns (ok, result)
      - ok: False if model missing/error
      - result: {"prediction": int, "reason": str?} on success or {"error": str}
    """
    if not is_model_available():
        return False, {"error": "Model not trained yet."}
    try:
        model = load_model()
        features = np.array([
            data["surface_temp"],
            data["ambient_temp"],
            data["accel_x"],
            data["accel_y"],
            data["accel_z"]
        ]).reshape(1, -1)
        prediction = int(model.predict(features)[0])

        # Identify primary anomalous sensor (rule-based deviation from baseline)
        deviations = {
            "surface_temp": abs(data["surface_temp"] - 23.5),
            "ambient_temp": abs(data["ambient_temp"] - 24.2),
            "accel_x": abs(data["accel_x"] - 1.03),
            "accel_y": abs(data["accel_y"] - 0.00),
            "accel_z": abs(data["accel_z"] - -0.08)
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

        # Only attach reason for non-normal states
        if prediction in (1, 2):
            return True, {"prediction": prediction, "reason": cause}
        return True, {"prediction": prediction}
    except Exception as e:
        return False, {"error": str(e)}

def retrain_model(features, labels):
    """
    Train or retrain the ML model in the cloud and save it.
    """
    try:
        X = np.array(features)
        y = np.array(labels)
        model = LogisticRegression()
        model.fit(X, y)
        joblib.dump(model, MODEL_PATH)
        return True, "Model retrained and saved."
    except Exception as e:
        return False, {"error": f"Retraining error: {e}"}
