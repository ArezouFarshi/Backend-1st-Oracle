def finalize_event(panel_id: str, result: dict):
    try:
        prediction = result.get("prediction", 0)
        if prediction == 1:
            status = f"Panel {panel_id}: Fault detected"
        elif prediction == 2:
            status = f"Panel {panel_id}: Warning detected"
        else:
            status = f"Panel {panel_id}: Normal operation"
        return True, status
    except Exception as e:
        return False, f"Finalize error: {e}"
