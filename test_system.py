import sys
sys.path.insert(0, '.')

print('Testing system initialization...')
print()

# Test geometry module
from backend.geometry import calculate_angle
print('✓ geometry module loaded')

# Test squat counter
from backend.squat import SquatCounter
squat = SquatCounter()
print('✓ SquatCounter initialized')

# Test MoveNet local (should fail gracefully)
try:
    from pose.local.movenet_local import MoveNetLocal
    movenet = MoveNetLocal()
    if movenet.interpreter:
        print('✓ MoveNet model loaded (using TFLite)')
    else:
        print('✓ MoveNet initialized (will fallback to MediaPipe)')
except Exception as e:
    print(f'  MoveNet Error: {e}')

# Test main pose detector
from backend.pose import PoseDetector
pose = PoseDetector()
print(f'✓ PoseDetector initialized (backend: {pose.backend})')
print()
print('✓ All systems ready!')
