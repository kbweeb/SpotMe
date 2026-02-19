import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from geometry import calculate_angle

class SquatCounter:
    def __init__(self):
        self.stage = "up"
        self.reps = 0

    def analyze(self, landmarks):
        # Validate that all required landmarks are present
        required_keys = ["hip", "knee", "ankle", "shoulder"]
        if not landmarks or not all(k in landmarks for k in required_keys):
            return self.reps, "Incomplete pose detection"
        
        hip = landmarks["hip"]
        knee = landmarks["knee"]
        ankle = landmarks["ankle"]
        shoulder = landmarks["shoulder"]

        try:
            knee_angle = calculate_angle(hip, knee, ankle)
            hip_angle = calculate_angle(shoulder, hip, knee)
        except Exception as e:
            print(f"Error calculating angles: {e}")
            return self.reps, f"Error calculating angles"

        feedback = None

        if knee_angle < 110 and hip_angle < 120 and self.stage == "up":
            self.stage = "down"
            feedback = "Good depth"

        if knee_angle > 160 and self.stage == "down":
            self.stage = "up"
            self.reps += 1
            feedback = f"Rep {self.reps}"

        return self.reps, feedback
