import time

# In-memory panel status
panel_status = {
    "ID_27_C_42": {"state": "unknown", "reason": "", "ts": 0}
}

def finalize_event(panel_id, result):
    ts = int(time.time())
    if result["fault"]:
        state = "red"
        reason = f"ML predicted fault with score {result['score']}"
    else:
        state = "blue"
        reason = f"normal (score: {result['score']})"

    panel_status[panel_id] = {"state": state, "reason": reason, "ts": ts}
    return True, panel_status[panel_id]
