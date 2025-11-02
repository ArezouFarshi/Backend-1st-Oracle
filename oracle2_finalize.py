def finalize_event(panel_id: str, result: dict):
    """
    Oracle 2: Finalize ML output.
    Here you could add thresholds, blockchain anchoring, etc.
    For now, just return a status string.
    """
    try:
        prediction = result.get("prediction")
        if prediction == 1:
            status = f"Panel {panel_id}: Fault detected"
        else:
            status = f"Panel {panel_id}: Normal operation"
        return True, status
    except Exception as e:
        return False, f"Finalize error: {e}"
