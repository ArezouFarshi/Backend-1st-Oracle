import time

panel_status = {}

def finalize_event(panel_id, result):
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
