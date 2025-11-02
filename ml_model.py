import joblib
import numpy as np

# Load trained model
model = joblib.load("fault_model.pkl")

def predict_fault(data: dict):
    """
    Run ML model on validated data.
    """
    try:
        features = np.array([
            data["temperature"],
            data["humidity"],
            data["tilt"]
        ]).reshape(1, -1)

        prediction = model.predict(features)[0]
        return True, {"prediction": int(prediction)}
    except Exception as e:
        return False, {"error": str(e)}
