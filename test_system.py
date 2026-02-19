import sys
sys.path.insert(0, '.')

print('Testing system initialization...')
print()

# Test geometry module
from backend.geometry import calculate_angle
print('[OK] geometry module loaded')

# Test squat counter
from backend.squat import SquatCounter
squat = SquatCounter()
print('[OK] SquatCounter initialized')

# Test MoveNet local (should fail gracefully)
from backend.pose import PoseDetector
try:
    MoveNetLocal = PoseDetector._load_movenet_class()
    if MoveNetLocal is None:
        print('[OK] MoveNet module not found (fallback will be used)')
    else:
        movenet = MoveNetLocal()
        if movenet.interpreter:
            print('[OK] MoveNet model loaded (using TFLite)')
        else:
            print('[OK] MoveNet initialized (will fallback to MediaPipe)')
except Exception as e:
    print(f'  MoveNet Error: {e}')

# Test main pose detector
pose = PoseDetector()
print(f'[OK] PoseDetector initialized (backend: {pose.backend})')
print()
print('[OK] All systems ready!')
