"""Shared keypoints utilities and standard output contract.

Standard keypoint format:
{
  "nose": [x, y, score],
  "left_shoulder": [x, y, score],
  "right_shoulder": [x, y, score],
  ...
}

Coordinates: normalized 0..1 when possible; score in 0..1.
"""
from typing import Dict, Tuple

JOINTS_OF_INTEREST = [
    "nose",
    "left_shoulder",
    "right_shoulder",
    "left_hip",
    "right_hip",
    "left_knee",
    "right_knee",
    "left_ankle",
    "right_ankle",
]


def to_pixel(coords: Tuple[float, float], frame_shape: Tuple[int, int]) -> Tuple[int, int]:
    h, w = frame_shape[:2]
    x, y = coords
    if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
        return int(x * w), int(y * h)
    return int(x), int(y)


def standardize_from_simple(landmarks: Dict[str, Tuple[float, float]], score: float = 1.0) -> Dict[str, Tuple[float, float, float]]:
    """Take a simple landmarks dict (shoulder/hip/knee/ankle) and expand to standard keys.
    Missing keys will be omitted.
    """
    out = {}
    # Map simplified landmarks to standard keys
    if "shoulder" in landmarks:
        sx, sy = landmarks["shoulder"]
        out["left_shoulder"] = [sx, sy, score]
        out["right_shoulder"] = [sx, sy, score]
    if "hip" in landmarks:
        hx, hy = landmarks["hip"]
        out["left_hip"] = [hx, hy, score]
        out["right_hip"] = [hx, hy, score]
    if "knee" in landmarks:
        kx, ky = landmarks["knee"]
        out["left_knee"] = [kx, ky, score]
        out["right_knee"] = [kx, ky, score]
    if "ankle" in landmarks:
        ax, ay = landmarks["ankle"]
        out["left_ankle"] = [ax, ay, score]
        out["right_ankle"] = [ax, ay, score]

    return out
