import time

# In-memory dictionary to store panel status
# Key = panel_id, Value = {state, reason, timestamp}
panel_status = {}

def finalize_event(panel_id, result):
    """
    Final validation oracle. Updates the in-memory status of the panel
    using the prediction result from the ML model.
    """
    ts = int(time.time())

    if result["fault"]:
        state = "red"
        reason = f"ML predicted fault with score {result['score']}"
    else:
        state = "blue"
        reason = f"Normal (score: {result['score']})"

    # Save panel's current status
    panel_status[panel_id] = {
        "state": state,
        "reason": reason,
        "ts": ts
    }

    return True, panel_status[panel_id]
