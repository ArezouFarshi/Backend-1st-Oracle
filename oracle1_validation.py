def validate_payload(data: dict):
    required = ["panel_id", "surface_temp", "ambient_temp", "accel_x", "accel_y", "accel_z"]
    
    for field in required:
        # Check if field exists and is not None
        if field not in data or data[field] is None:
            return False, {"reason": f"System error: {field} missing or null"}
        
        # Check for sensor disconnected or stuck (flat zero, which often means disconnected wire)
        if isinstance(data[field], (int, float)) and abs(data[field]) < 0.001 and field != "panel_id":
            return False, {"reason": f"System error: {field} possibly disconnected (value={data[field]})"}

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

    # Acceleration checks
    for axis in ['accel_x', 'accel_y', 'accel_z']:
        acc = abs(data[axis])
        if acc > 2:
            return False, {"reason": f"{axis} FAULT (value: {data[axis]})"}
        if acc > 1:
            return True, {"warning": f"{axis} WARNING (value: {data[axis]})", **data}

    # Everything is valid
    return True, data
