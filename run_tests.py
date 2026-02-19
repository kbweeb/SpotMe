#!/usr/bin/env python
"""Comprehensive system test for GymBuddy AI."""
import os
import sys


def log_ok(message: str) -> None:
    print(f"  [OK] {message}")


def log_fail(message: str) -> None:
    print(f"  [FAIL] {message}")


def log_warn(message: str) -> None:
    print(f"  [WARN] {message}")


print("=" * 60)
print("GymBuddy AI System - Comprehensive Test")
print("=" * 60)

failures = 0

# Test 1: Geometry Module
print("\n[1/5] Testing Geometry Module...")
try:
    from backend.geometry import calculate_angle
    import numpy as np

    a = np.array([0, 0])
    b = np.array([0, 1])
    c = np.array([1, 1])
    angle = calculate_angle(a, b, c)
    assert 89 < angle < 91, f"Expected ~90 deg, got {angle} deg"
    log_ok("Geometry calculations working correctly")
except Exception as e:
    failures += 1
    log_fail(f"Error: {e}")

# Test 2: Squat Counter
print("\n[2/5] Testing Squat Counter...")
try:
    sys.path.insert(0, "backend")
    from squat import SquatCounter

    squat = SquatCounter()
    assert squat.reps == 0
    assert squat.stage == "up"
    log_ok("SquatCounter initialized successfully")
except Exception as e:
    failures += 1
    log_fail(f"Error: {e}")

# Test 3: Models Check
print("\n[3/5] Checking Models...")
try:
    model_path = "backend/models/movenet_lightning.tflite"
    if os.path.exists(model_path):
        size = os.path.getsize(model_path)
        log_ok(f"MoveNet model found ({size} bytes)")
    else:
        log_warn("MoveNet model not found - fallback backend may be used")
except Exception as e:
    failures += 1
    log_fail(f"Error: {e}")

# Test 4: Pose Detector with Sample Frame
print("\n[4/5] Testing Pose Detection...")
try:
    import numpy as np
    from pose import PoseDetector

    detector = PoseDetector()
    log_ok(f"PoseDetector initialized (backend: {detector.backend})")

    # A blank frame should not crash the pipeline; landmark detection is optional here.
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    landmarks = detector.process(dummy_frame)

    if landmarks:
        assert "shoulder" in landmarks
        assert "hip" in landmarks
        assert "knee" in landmarks
        assert "ankle" in landmarks
        log_ok("Pose detection returned expected keypoints")
    else:
        log_warn("No landmarks detected on blank test frame (expected in many setups)")
except Exception as e:
    failures += 1
    log_fail(f"Error: {e}")

# Test 5: Complete Pipeline
print("\n[5/5] Testing Complete Pipeline...")
try:
    import numpy as np
    from squat import SquatCounter

    detector = PoseDetector()
    counter = SquatCounter()

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    landmarks = detector.process(frame)
    if landmarks:
        reps, feedback = counter.analyze(landmarks)
        log_ok("Complete pipeline processed test frame")
        print(f"    - Reps: {reps}")
        print(f"    - Backend: {detector.backend}")
        if feedback:
            print(f"    - Feedback: {feedback}")
    else:
        log_warn("Pipeline ran but no landmarks were produced for blank frame")
except Exception as e:
    failures += 1
    log_fail(f"Error: {e}")

print("\n" + "=" * 60)
if failures == 0:
    print("[OK] SYSTEM CHECKS PASSED")
else:
    print(f"[FAIL] SYSTEM CHECKS FAILED ({failures} failure(s))")
print("=" * 60)

print("\nKey Information:")
print("  - AI Framework: MediaPipe (with fallback)")
print(f"  - Python Version: {sys.version.split()[0]}")
print("  - Status: READY FOR LOCAL DEVELOPMENT" if failures == 0 else "  - Status: ACTION REQUIRED")
print("\nNext Steps:")
print("  1. Start backend: python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8010")
print("  2. Start frontend: cd frontend && npm run dev -- --host 127.0.0.1 --port 5173")
print("=" * 60)

if failures:
    raise SystemExit(1)
