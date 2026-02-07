import mediapipe as mp
import cv2

mp_pose = mp.solutions.pose

class PoseDetector:
    def __init__(self):
        self.pose = mp_pose.Pose(
            model_complexity=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )

    def process(self, frame):
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(image)

        if not results.pose_landmarks:
            return None

        lm = results.pose_landmarks.landmark

        return {
            "shoulder": (lm[11].x, lm[11].y),
            "hip": (lm[23].x, lm[23].y),
            "knee": (lm[25].x, lm[25].y),
            "ankle": (lm[27].x, lm[27].y)
        }
