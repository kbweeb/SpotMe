import cv2
import numpy as np
import os
import urllib.request


class PoseDetector:
    """Pose detector that tries MediaPipe `solutions`, then `tasks`, then OpenPose (OpenCV DNN), then a fallback.

    - `process(frame)` returns a dict with keys: `shoulder`,`hip`,`knee`,`ankle` as (x,y).
      Coordinates are normalized (0..1) for ML-based detectors, or pixel coords for fallback.
    """

    def __init__(self):
        self.backend = None
        self.pose = None
        self.detector = None
        self.mp = None

        # Try local MoveNet (TFLite) first
        try:
            import sys
            import os
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            from pose.local.movenet_local import MoveNetLocal
            movenet = MoveNetLocal()
            if getattr(movenet, 'interpreter', None) is not None:
                self.detector = movenet
                self.backend = "movenet_local"
                print("✓ PoseDetector: using MoveNet local TFLite")
                return
        except Exception:
            pass

        # Try MediaPipe solutions API
        try:
            import mediapipe as mp
            if hasattr(mp, "solutions"):
                self.mp = mp
                self.backend = "solutions"
                self.mp_pose = mp.solutions.pose
                self.pose = self.mp_pose.Pose(
                    static_image_mode=False,
                    model_complexity=1,
                    smooth_landmarks=True,
                    enable_segmentation=False,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5,
                )
                self.mp_draw = mp.solutions.drawing_utils
                print("✓ PoseDetector: using mediapipe.solutions")
                return
        except Exception:
            pass

        # Try MediaPipe Tasks API
        try:
            import mediapipe as mp
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            
            # Download model if not exists
            model_path = "pose_landmarker_lite.task"
            if not os.path.exists(model_path):
                print("Downloading MediaPipe pose model...")
                model_url = "https://storage.googleapis.com/mediapipe-tasks/python/pose_landmarker/lite/pose_landmarker_lite.task"
                try:
                    urllib.request.urlretrieve(model_url, model_path)
                    print("✓ Model downloaded")
                except:
                    print("Failed to download model")
                    raise Exception("Could not download model")

            self.mp = mp
            base_options = python.BaseOptions(model_asset_path=model_path)
            options = vision.PoseLandmarkerOptions(
                base_options=base_options,
                output_segmentation_masks=False,
                min_pose_detection_confidence=0.5,
                min_pose_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self.detector = vision.PoseLandmarker.create_from_options(options)
            self.backend = "tasks"
            print("✓ PoseDetector: using mediapipe.tasks")
            return
        except Exception as e:
            pass

        # Try OpenPose (OpenCV DNN)
        try:
            from .op_pose import OpenPoseDetector

            self.detector = OpenPoseDetector()
            if self.detector and getattr(self.detector, "net", None) is not None:
                self.backend = "openpose"
                print("✓ PoseDetector: using OpenPose (OpenCV DNN)")
                return
        except Exception:
            pass

        # Fallback
        self.backend = "fallback"
        print("Warning: PoseDetector using fallback estimator")

    def process(self, frame):
        h, w = frame.shape[:2]

        if self.backend == "solutions":
            try:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                res = self.pose.process(rgb)
                if res.pose_landmarks:
                    lm = res.pose_landmarks.landmark
                    return {
                        "shoulder": (lm[11].x, lm[11].y),
                        "hip": (lm[23].x, lm[23].y),
                        "knee": (lm[25].x, lm[25].y),
                        "ankle": (lm[27].x, lm[27].y),
                    }
            except Exception as e:
                print(f"PoseDetector (solutions) error: {e}")
                return None

        if self.backend == "tasks":
            try:
                mp_img = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                result = self.detector.detect(mp_img)
                if hasattr(result, "pose_landmarks") and result.pose_landmarks:
                    lm = result.pose_landmarks.landmark
                    return {
                        "shoulder": (lm[11].x, lm[11].y),
                        "hip": (lm[23].x, lm[23].y),
                        "knee": (lm[25].x, lm[25].y),
                        "ankle": (lm[27].x, lm[27].y),
                    }
            except Exception as e:
                print(f"PoseDetector (tasks) error: {e}")
                return None

        if self.backend == "openpose":
            try:
                return self.detector.detect(frame)
            except Exception as e:
                print(f"PoseDetector (openpose) error: {e}")
                return None

        # fallback: return rough estimates in pixel coordinates
        if self.backend == "fallback":
            return self._detect_fallback(frame)

        return None

    def _detect_fallback(self, frame):
        """Smart fallback using OpenCV face detection and simple heuristics."""
        h, w = frame.shape[:2]
        
        # Try to detect faces/heads using cascade classifier
        try:
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                x, y, faceW, faceH = faces[0]
                # If we detect a face, infer body position
                shoulder_y = y + faceH + faceH // 3
                hip_y = shoulder_y + faceH * 1.5
                knee_y = hip_y + faceH * 1.5
                ankle_y = knee_y + faceH
                
                center_x = x + faceW // 2
                
                return {
                    "shoulder": (center_x / w, min(shoulder_y / h, 1.0)),
                    "hip": (center_x / w, min(hip_y / h, 1.0)),
                    "knee": (center_x / w, min(knee_y / h, 1.0)),
                    "ankle": (center_x / w, min(ankle_y / h, 1.0)),
                }
        except:
            pass
        
        # Default fallback with normalized coordinates
        return {
            "shoulder": (w * 0.5 / w, h * 0.25 / h),
            "hip": (w * 0.5 / w, h * 0.5 / h),
            "knee": (w * 0.5 / w, h * 0.75 / h),
            "ankle": (w * 0.5 / w, h * 0.95 / h),
        }

    def draw_on(self, frame, landmarks):
        """Helper to draw landmarks and connections on `frame` for debugging."""
        if not landmarks:
            return frame

        h, w = frame.shape[:2]
        pts = {}
        for k, (x, y) in landmarks.items():
            if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
                px, py = int(x * w), int(y * h)
            else:
                px, py = int(x), int(y)
            pts[k] = (px, py)
            cv2.circle(frame, (px, py), 6, (0, 255, 255), -1)

        seq = ["shoulder", "hip", "knee", "ankle"]
        for i in range(len(seq) - 1):
            a = pts.get(seq[i])
            b = pts.get(seq[i + 1])
            if a and b:
                cv2.line(frame, a, b, (0, 200, 255), 3)

        return frame
