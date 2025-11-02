import time

# In-memory dictionary to store panel status
# Key = panel_id, Value = {state, reason, timestamp}
panel_status = {}

def finalize_event(panel_id, result):
    """
    Final validation oracle. Updates the in-memory status of the panel
    using the prediction result from the ML model, applying the platform's fixed color logic.
    """
    ts = int(time.time())

    if result.get("error"):
        state = "purple"
        reason = "Sensor or ML system/platform error"

    elif result["fault"]:
        state = "red"
        reason = f"Confirmed fault (urgent) — ML score: {result['score']}"

    else:
        state = "blue"
        reason = f"Installed and healthy — ML score: {result['score']}"

    panel_status[panel_id] = {
        "state": state,
        "reason": reason,
        "ts": ts
    }

    return True, panel_status[panel_id]
