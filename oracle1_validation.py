def validate_payload(data: dict):
    required = ["panel_id", "surface_temp", "ambient_temp", "accel_x", "accel_y", "accel_z"]
    for field in required:
        if field not in data:
            return False, {"reason": f"Missing field: {field}"}

    # Surface temperature checks
    st = data["surface_temp"]
    if st < -15 or st > 85:
        return False, {"reason": "Surface temperature FAULT"}
    if st < -10 or st > 75:
        return True, {"warning": "Surface temperature WARNING", **data}

    # Ambient temperature checks
    at = data["ambient_temp"]
    if at < -20 or at > 55:
        return False, {"reason": "Ambient temperature FAULT"}
    if at < -10 or at > 45:
        return True, {"warning": "Ambient temperature WARNING", **data}

    # Acceleration checks (simple fault threshold for demo; you can refine)
    # For example, any axis > |2g| is abnormal for a panel
    for axis in ['accel_x', 'accel_y', 'accel_z']:
        acc = abs(data[axis])
        if acc > 2:
            return False, {"reason": f"{axis} FAULT (value: {data[axis]})"}
        if acc > 1:
            return True, {"warning": f"{axis} WARNING (value: {data[axis]})", **data}

    return True, data
