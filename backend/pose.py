import os
import importlib.util
import urllib.request

import cv2


TASK_MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
TASK_MODEL_PATH = os.path.join(TASK_MODEL_DIR, "pose_landmarker_lite.task")
MOVENET_MODULE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "pose", "local", "movenet_local.py")
)
TASK_MODEL_URLS = [
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task",
    "https://storage.googleapis.com/mediapipe-tasks/python/pose_landmarker/lite/pose_landmarker_lite.task",
]
MIN_KEYPOINT_SCORE = 0.2


class PoseDetector:
    """Unified pose detector with multiple backends and a safe fallback."""

    _task_model_error = None

    def __init__(self):
        self.backend = None
        self.pose = None
        self.detector = None
        self.mp = None

        # 1) Try local MoveNet (TFLite)
        try:
            movenet_cls = self._load_movenet_class()
            if movenet_cls is not None:
                movenet = movenet_cls()
                if getattr(movenet, "interpreter", None) is not None:
                    self.detector = movenet
                    self.backend = "movenet_local"
                    print("PoseDetector: using MoveNet local TFLite")
                    return
        except Exception:
            pass

        # 2) Try MediaPipe solutions API
        try:
            import mediapipe as mp

            if hasattr(mp, "solutions") and hasattr(mp.solutions, "pose"):
                self.mp = mp
                self.backend = "solutions"
                self.pose = mp.solutions.pose.Pose(
                    static_image_mode=False,
                    model_complexity=1,
                    smooth_landmarks=True,
                    enable_segmentation=False,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5,
                )
                print("PoseDetector: using mediapipe.solutions")
                return
        except Exception:
            pass

        # 3) Try MediaPipe Tasks API
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision

            model_path = self._ensure_pose_task_model()
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.PoseLandmarkerOptions(
                base_options=base_options,
                output_segmentation_masks=False,
                min_pose_detection_confidence=0.5,
                min_pose_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self.mp = mp
            self.detector = vision.PoseLandmarker.create_from_options(options)
            self.backend = "tasks"
            print("PoseDetector: using mediapipe.tasks")
            return
        except Exception:
            pass

        # 4) Try OpenPose (OpenCV DNN)
        try:
            try:
                from .op_pose import OpenPoseDetector
            except ImportError:
                from op_pose import OpenPoseDetector

            detector = OpenPoseDetector()
            if detector and getattr(detector, "net", None) is not None:
                self.detector = detector
                self.backend = "openpose"
                print("PoseDetector: using OpenPose (OpenCV DNN)")
                return
        except Exception:
            pass

        # 5) Fallback
        self.backend = "fallback"
        print("Warning: PoseDetector using fallback estimator")

    @classmethod
    def _ensure_pose_task_model(cls):
        os.makedirs(TASK_MODEL_DIR, exist_ok=True)
        if os.path.exists(TASK_MODEL_PATH):
            return TASK_MODEL_PATH

        if cls._task_model_error:
            raise RuntimeError(cls._task_model_error)

        last_error = None
        for model_url in TASK_MODEL_URLS:
            try:
                print(f"Downloading MediaPipe pose model from: {model_url}")
                urllib.request.urlretrieve(model_url, TASK_MODEL_PATH)
                print("Pose task model downloaded")
                return TASK_MODEL_PATH
            except Exception as err:
                last_error = err

        cls._task_model_error = f"Could not download pose task model: {last_error}"
        raise RuntimeError(cls._task_model_error)

    @staticmethod
    def _load_movenet_class():
        if not os.path.exists(MOVENET_MODULE_PATH):
            return None
        spec = importlib.util.spec_from_file_location(
            "gymbuddy_movenet_local", MOVENET_MODULE_PATH
        )
        if not spec or not spec.loader:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, "MoveNetLocal", None)

    @staticmethod
    def _avg_xy(point_a, point_b):
        if point_a and point_b:
            return ((point_a[0] + point_b[0]) / 2.0, (point_a[1] + point_b[1]) / 2.0)
        if point_a:
            return point_a
        if point_b:
            return point_b
        return None

    @staticmethod
    def _avg_scored_point(point_a, point_b):
        valid_points = []
        for point in (point_a, point_b):
            if not point or len(point) < 2:
                continue
            score = float(point[2]) if len(point) > 2 else 1.0
            if score >= MIN_KEYPOINT_SCORE:
                valid_points.append((float(point[0]), float(point[1])))
        if len(valid_points) == 2:
            return (
                (valid_points[0][0] + valid_points[1][0]) / 2.0,
                (valid_points[0][1] + valid_points[1][1]) / 2.0,
            )
        if len(valid_points) == 1:
            return valid_points[0]
        return None

    def _from_movenet(self, keypoints):
        if not keypoints:
            return None

        shoulder = self._avg_scored_point(
            keypoints.get("left_shoulder"), keypoints.get("right_shoulder")
        )
        hip = self._avg_scored_point(keypoints.get("left_hip"), keypoints.get("right_hip"))
        knee = self._avg_scored_point(
            keypoints.get("left_knee"), keypoints.get("right_knee")
        )
        ankle = self._avg_scored_point(
            keypoints.get("left_ankle"), keypoints.get("right_ankle")
        )

        if shoulder and hip and knee and ankle:
            return {
                "shoulder": shoulder,
                "hip": hip,
                "knee": knee,
                "ankle": ankle,
            }
        return None

    @staticmethod
    def _landmark_xy(landmark):
        if landmark is None:
            return None
        return float(landmark.x), float(landmark.y)

    def process(self, frame):
        if self.backend == "movenet_local":
            try:
                return self._from_movenet(self.detector.detect(frame))
            except Exception as err:
                print(f"PoseDetector (movenet_local) error: {err}")
                return None

        if self.backend == "solutions":
            try:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = self.pose.process(rgb)
                if result.pose_landmarks:
                    landmarks = result.pose_landmarks.landmark
                    shoulder = self._avg_xy(
                        self._landmark_xy(landmarks[11]),
                        self._landmark_xy(landmarks[12]),
                    )
                    hip = self._avg_xy(
                        self._landmark_xy(landmarks[23]),
                        self._landmark_xy(landmarks[24]),
                    )
                    knee = self._avg_xy(
                        self._landmark_xy(landmarks[25]),
                        self._landmark_xy(landmarks[26]),
                    )
                    ankle = self._avg_xy(
                        self._landmark_xy(landmarks[27]),
                        self._landmark_xy(landmarks[28]),
                    )
                    if shoulder and hip and knee and ankle:
                        return {
                            "shoulder": shoulder,
                            "hip": hip,
                            "knee": knee,
                            "ankle": ankle,
                        }
            except Exception as err:
                print(f"PoseDetector (solutions) error: {err}")
                return None

        if self.backend == "tasks":
            try:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb)
                result = self.detector.detect(mp_image)
                pose_landmarks = getattr(result, "pose_landmarks", None)
                if pose_landmarks:
                    first_pose = pose_landmarks[0]
                    if hasattr(first_pose, "landmark"):
                        first_pose = first_pose.landmark
                    shoulder = self._avg_xy(
                        self._landmark_xy(first_pose[11]),
                        self._landmark_xy(first_pose[12]),
                    )
                    hip = self._avg_xy(
                        self._landmark_xy(first_pose[23]),
                        self._landmark_xy(first_pose[24]),
                    )
                    knee = self._avg_xy(
                        self._landmark_xy(first_pose[25]),
                        self._landmark_xy(first_pose[26]),
                    )
                    ankle = self._avg_xy(
                        self._landmark_xy(first_pose[27]),
                        self._landmark_xy(first_pose[28]),
                    )
                    if shoulder and hip and knee and ankle:
                        return {
                            "shoulder": shoulder,
                            "hip": hip,
                            "knee": knee,
                            "ankle": ankle,
                        }
            except Exception as err:
                print(f"PoseDetector (tasks) error: {err}")
                return None

        if self.backend == "openpose":
            try:
                return self.detector.detect(frame)
            except Exception as err:
                print(f"PoseDetector (openpose) error: {err}")
                return None

        if self.backend == "fallback":
            return self._detect_fallback(frame)

        return None

    def _detect_fallback(self, frame):
        """Fallback using face detection + simple body heuristics."""
        h, w = frame.shape[:2]
        try:
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            if len(faces) > 0:
                x, y, face_w, face_h = faces[0]
                shoulder_y = y + face_h + face_h // 3
                hip_y = shoulder_y + face_h * 1.5
                knee_y = hip_y + face_h * 1.5
                ankle_y = knee_y + face_h
                center_x = x + face_w // 2
                return {
                    "shoulder": (center_x / w, min(shoulder_y / h, 1.0)),
                    "hip": (center_x / w, min(hip_y / h, 1.0)),
                    "knee": (center_x / w, min(knee_y / h, 1.0)),
                    "ankle": (center_x / w, min(ankle_y / h, 1.0)),
                }
        except Exception:
            pass

        return {
            "shoulder": (0.5, 0.25),
            "hip": (0.5, 0.5),
            "knee": (0.5, 0.75),
            "ankle": (0.5, 0.95),
        }

    def draw_on(self, frame, landmarks):
        """Draw landmarks and basic connections on a frame."""
        if not landmarks:
            return frame

        h, w = frame.shape[:2]
        points = {}
        for key, (x, y) in landmarks.items():
            if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
                px, py = int(x * w), int(y * h)
            else:
                px, py = int(x), int(y)
            points[key] = (px, py)
            cv2.circle(frame, (px, py), 6, (0, 255, 255), -1)

        ordered = ["shoulder", "hip", "knee", "ankle"]
        for idx in range(len(ordered) - 1):
            start = points.get(ordered[idx])
            end = points.get(ordered[idx + 1])
            if start and end:
                cv2.line(frame, start, end, (0, 200, 255), 3)

        return frame
