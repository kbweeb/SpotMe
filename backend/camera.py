import cv2
import numpy as np


def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - \
              np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180.0:
        angle = 360 - angle

    return angle


def draw_skeleton(image, landmarks):
    """Draw simple skeleton (shoulder->hip->knee->ankle) on image.

    landmarks: dict with keys 'shoulder','hip','knee','ankle' -> (x,y)
    Coordinates may be normalized (0..1) or pixel coordinates.
    """
    h, w = image.shape[:2]

    # Convert landmarks to pixel coords if normalized
    pts = {}
    for k, (x, y) in landmarks.items():
        if x <= 1.0 and y <= 1.0:
            px, py = int(x * w), int(y * h)
        else:
            px, py = int(x), int(y)
        pts[k] = (px, py)

    # Draw joints
    for p in pts.values():
        cv2.circle(image, p, 6, (0, 255, 255), -1)

    # Draw lines: shoulder -> hip -> knee -> ankle
    seq = ["shoulder", "hip", "knee", "ankle"]
    for i in range(len(seq)-1):
        a = pts.get(seq[i])
        b = pts.get(seq[i+1])
        if a and b:
            cv2.line(image, a, b, (0, 200, 255), 3)


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera. Make sure a camera is connected and not in use by another application.")
        return

    counter = 0

    print("Starting GymBuddy Squat Detector")
    print("Press 'q' to quit")

    # Try to enable pose detection if available
    try:
        from pose import PoseDetector
        from squat import SquatCounter

        pose_detector = PoseDetector()
        squat_counter = SquatCounter()
        use_pose_detection = True
        print("✓ Pose detection enabled")
    except Exception as e:
        print(f"⚠ Warning: Pose detection unavailable: {e}")
        use_pose_detection = False

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        image = frame.copy()

        try:
            if use_pose_detection:
                landmarks = pose_detector.process(frame)
                if landmarks:
                    # landmarks may be MoveNet full keypoints or simple shoulder/hip/knee/ankle
                    # If full keypoints (left_shoulder etc), convert to simple averages for squat logic
                    if isinstance(landmarks, dict) and 'left_shoulder' in landmarks:
                        # compute averages for key joints expected by SquatCounter
                        def avg_key(a, b):
                            ka = landmarks.get(a)
                            kb = landmarks.get(b)
                            if ka and kb:
                                # both are [x,y,score] (normalized)
                                return ((ka[0]+kb[0])/2.0, (ka[1]+kb[1])/2.0)
                            if ka:
                                return (ka[0], ka[1])
                            if kb:
                                return (kb[0], kb[1])
                            return None

                        simple = {}
                        s = avg_key('left_shoulder', 'right_shoulder')
                        h = avg_key('left_hip', 'right_hip')
                        k = avg_key('left_knee', 'right_knee')
                        a = avg_key('left_ankle', 'right_ankle')
                        if s: simple['shoulder'] = s
                        if h: simple['hip'] = h
                        if k: simple['knee'] = k
                        if a: simple['ankle'] = a

                        # draw full keypoints for visibility
                        for name, v in landmarks.items():
                            if v:
                                x, y, score = v
                                h_img, w_img = image.shape[:2]
                                px, py = (int(x*w_img), int(y*h_img)) if 0.0<=x<=1.0 and 0.0<=y<=1.0 else (int(x), int(y))
                                cv2.circle(image, (px, py), 4, (255, 200, 0), -1)

                        if simple:
                            reps, feedback = squat_counter.analyze(simple)
                            counter = reps
                            if feedback:
                                cv2.putText(image, feedback, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                    else:
                        # assume simple dict already
                        draw_skeleton(image, landmarks)
                        reps, feedback = squat_counter.analyze(landmarks)
                        counter = reps
                        if feedback:
                            cv2.putText(image, feedback, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                else:
                    cv2.putText(image, "No pose detected", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            # Draw rep counter
            cv2.rectangle(image, (0, 0), (300, 100), (0, 0, 0), -1)
            cv2.putText(image, 'REPS', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(image, str(counter), (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

            cv2.imshow('GymBuddy – Squat Detection', image)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                print("Exiting...")
                break

        except Exception as e:
            print(f"Error processing frame: {e}")
            continue

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
