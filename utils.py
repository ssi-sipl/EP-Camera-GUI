import cv2
import numpy as np

# ===================== CROSSHAIR =====================
def overlay_crosshair(frame):
    """Draw a red crosshair at center of frame."""
    if frame is None or frame.size == 0:
        return frame
    out = frame.copy()
    h, w = out.shape[:2]
    cx, cy = w // 2, h // 2
    size = max(10, min(w, h) // 20)
    cv2.line(out, (cx - size, cy), (cx + size, cy), (0, 0, 255), 2)
    cv2.line(out, (cx, cy - size), (cx, cy + size), (0, 0, 255), 2)
    return out


# ===================== THERMAL HELPERS =====================
def build_sumcheck(val, func, opcode):
    val = int(val)
    ranges = {
        "brightness": (10, 250),
        "contrast": (10, 250),
        "reference_image": (0, 128),
        "DDE_mode": (1, 3),
        "DDE_strength": (1, 128),
        "zoom": (1, 16),
    }
    if func in ranges:
        mn, mx = ranges[func]
        if not (mn <= val <= mx):
            raise ValueError(f"{func} must be between {mn} and {mx}")
    checksum = opcode + val
    return f"{checksum & 0xFF:02X} {(checksum >> 8) & 0xFF:02X}"


def checksum_response(data):
    return sum(data) & 0xFFFF
