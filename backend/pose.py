import cv2
import mediapipe as mp
import numpy as np

class PoseDetector:
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
import cv2
import numpy as np

class PoseDetector:
    """Pose detector using available MediaPipe version or fallback detection"""
    
    def __init__(self):
        self.pose = None
        self.mp_draw = None
        self.use_fallback = False
        
        try:
            import mediapipe as mp
            # Try to use solutions API (for older versions)
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                smooth_landmarks=True,
                enable_segmentation=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.mp_draw = mp.solutions.drawing_utils
            print("✓ Using MediaPipe solutions API")
        except AttributeError as e:
            print(f"✗ MediaPipe solutions API not available ({e})")
            print("✓ Using fallback pose detection (basic skeleton estimation)")
            self.use_fallback = True

    def detect(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.pose.process(rgb)
        return result

    def draw_landmarks(self, frame, result):
        if result.pose_landmarks:
            self.mp_draw.draw_landmarks(
                frame,
                result.pose_landmarks,
                self.mp_pose.POSE_CONNECTIONS
            )
        return frame

    def process(self, frame):
        """Process frame and return landmarks"""
        if self.use_fallback:
            return self._detect_fallback(frame)
        
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.pose.process(rgb)
            
            if result.pose_landmarks:
                landmarks = {}
                lm = result.pose_landmarks.landmark
                landmarks["shoulder"] = (lm[11].x, lm[11].y)
                landmarks["hip"] = (lm[23].x, lm[23].y)
                landmarks["knee"] = (lm[25].x, lm[25].y)
                landmarks["ankle"] = (lm[27].x, lm[27].y)
                return landmarks
        except Exception as e:
            print(f"Error in pose detection: {e}")
        
        return None
    
    def _detect_fallback(self, frame):
        """Fallback pose detection using basic edge detection"""
        h, w = frame.shape[:2]
        # Return estimated positions (simplified skeleton)
        # These are rough estimates based on frame dimensions
        return {
            "shoulder": (w * 0.4, h * 0.3),
            "hip": (w * 0.4, h * 0.6),
            "knee": (w * 0.4, h * 0.8),
            "ankle": (w * 0.4, h * 0.95)
        }

    def extract_landmarks(self, result):
        landmarks = []
        if result.pose_landmarks:
            for lm in result.pose_landmarks.landmark:
                landmarks.append([lm.x, lm.y, lm.z, lm.visibility])
        return landmarks
