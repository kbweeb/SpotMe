from geometry import calculate_angle

class SquatCounter:
    def __init__(self):
        self.stage = "up"
        self.reps = 0

    def analyze(self, landmarks):
        hip = landmarks["hip"]
        knee = landmarks["knee"]
        ankle = landmarks["ankle"]
        shoulder = landmarks["shoulder"]

        knee_angle = calculate_angle(hip, knee, ankle)
        hip_angle = calculate_angle(shoulder, hip, knee)

        feedback = None

        if knee_angle < 110 and hip_angle < 120 and self.stage == "up":
            self.stage = "down"
            feedback = "Good depth"

        if knee_angle > 160 and self.stage == "down":
            self.stage = "up"
            self.reps += 1
            feedback = f"Rep {self.reps}"

        return self.reps, feedback
