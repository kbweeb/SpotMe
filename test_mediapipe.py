import sys
sys.path.insert(0, '.')

print('Testing MediaPipe directly...')

try:
    import mediapipe as mp
    print('✓ MediaPipe imported')
    
    # Check what's available
    print(f'✓ mp.solutions available: {hasattr(mp, "solutions")}')
    
    if hasattr(mp, "solutions"):
        mp_pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        print('✓ MediaPipe Pose initialized successfully!')
        
        # Test with a dummy frame
        import numpy as np
        dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = mp_pose.process(dummy_frame)
        print(f'✓ MediaPipe Pose processed frame: {result.pose_landmarks is not None}')
        
except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()
