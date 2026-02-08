import cv2
import numpy as np
import os

# Create the pose landmark detector
def create_pose_detector():
    model_path = os.path.join(os.path.dirname(__file__), 'pose_landmarker.task')
    
    # If model doesn't exist, download it or use default
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        output_segmentation_masks=False,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )
    return vision.PoseLandmarker.create_from_options(options)

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

def main():
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera. Make sure a camera is connected and not in use by another application.")
        return
    
    counter = 0
    stage = None
    
    print("Starting GymBuddy Squat Detector")
    print("Press 'q' to quit")
    
    # Try to import pose detection - will work if mediapipe is properly configured
    try:
        from pose import PoseDetector
        from squat import SquatCounter
        
        pose_detector = PoseDetector()
        squat_counter = SquatCounter()
        use_pose_detection = True
        print("✓ Pose detection enabled")
    except ImportError as e:
        print(f"⚠ Warning: Could not import pose detection modules: {e}")
        print("  Running in camera-only mode")
        use_pose_detection = False
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        try:
            image = frame.copy()
            
            if use_pose_detection:
                # Use the imported pose and squat detection
                landmarks = pose_detector.process(frame)
                
                if landmarks:
                    reps, feedback = squat_counter.analyze(landmarks)
                    counter = reps
                    
                    # Display angle feedback
                    if feedback:
                        cv2.putText(image, feedback, (50, 50),
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                else:
                    cv2.putText(image, "No pose detected", (50, 50),
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Draw rep counter
            cv2.rectangle(image, (0, 0), (300, 100), (0, 0, 0), -1)
            cv2.putText(image, 'REPS', (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(image, str(counter),
                        (10, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
            
            cv2.imshow('GymBuddy – Squat Detection', image)
            
            if cv2.waitKey(10) & 0xFF == ord('q'):
                print("Exiting...")
                break
        
        except Exception as e:
            print(f"Error processing frame: {e}")
            continue
    
    cap.release()
    cv2.destroyAllWindows()
    print("GymBuddy closed")

if __name__ == "__main__":
    main()
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.framework.formats import landmark_pb2
import numpy as np
import os

# Create the pose landmark detector
def create_pose_detector():
    model_path = os.path.join(os.path.dirname(__file__), 'pose_landmarker.task')
    
    # If model doesn't exist, download it or use default
    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        output_segmentation_masks=False,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )
    return vision.PoseLandmarker.create_from_options(options)

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

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera. Make sure a camera is connected and not in use by another application.")
    exit(1)

counter = 0
stage = None

with mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
) as pose:

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = pose.process(image)

        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        try:
            if results.pose_landmarks is not None:
                landmarks = results.pose_landmarks.landmark

                hip = [
                    landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y
                ]
                knee = [
                    landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y
                ]
                ankle = [
                    landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y
                ]

                angle = calculate_angle(hip, knee, ankle)

                cv2.putText(
                    image,
                    f"Angle: {int(angle)}",
                    (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 255, 255),
                    2
                )

                if angle > 160:
                    stage = "up"
                if angle < 90 and stage == "up":
                    stage = "down"
                    counter += 1
                    print(f"Rep: {counter}")

        except Exception as e:
            print(f"Error processing landmarks: {e}")

        cv2.rectangle(image, (0, 0), (300, 100), (0, 0, 0), -1)
        cv2.putText(image, 'REPS', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(image, str(counter),
                    (10, 80),
                    cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

        if results.pose_landmarks is not None:
            mp_drawing.draw_landmarks(
                image,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS
            )

        cv2.imshow('GymBuddy – Squat Detection', image)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
