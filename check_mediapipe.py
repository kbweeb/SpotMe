import sys
import mediapipe

# Try to import solutions different ways
print("MediaPipe version:", mediapipe.__version__)
print("MediaPipe __path__:", mediapipe.__path__)

# Try direct import
try:
    # Check if solutions is a namespace package
    import mediapipe.python.solutions.pose
    print("✓ Found via: mediapipe.python.solutions.pose")
except:
    pass

try:
    from mediapipe import python
    print("✓ mediapipe.python available")
    print("  Dir:", dir(python))
except:
    pass

# Check pip show
import subprocess
result = subprocess.run([sys.executable, "-m", "pip", "show", "mediapipe"], capture_output=True, text=True)
print("\nPip info:")
print(result.stdout)
