import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np

try:
    from .geometry import calculate_angle
except ImportError:
    from geometry import calculate_angle


DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "models", "exercise_classifier.json"
)
REQUIRED_KEYS = ("shoulder", "hip", "knee", "ankle")


@dataclass
class PredictionResult:
    exercise: str
    confidence: float
    source: str


def _point_distance(point_a, point_b):
    return float(math.dist(point_a, point_b))


def _safe_ratio(num, den):
    if den == 0:
        return 0.0
    return float(num / den)


def extract_features(landmarks):
    """Convert four normalized keypoints into a compact numeric feature vector."""
    if not landmarks:
        return None
    if not all(key in landmarks for key in REQUIRED_KEYS):
        return None

    shoulder = tuple(float(v) for v in landmarks["shoulder"])
    hip = tuple(float(v) for v in landmarks["hip"])
    knee = tuple(float(v) for v in landmarks["knee"])
    ankle = tuple(float(v) for v in landmarks["ankle"])

    try:
        knee_angle = float(calculate_angle(hip, knee, ankle))
        hip_angle = float(calculate_angle(shoulder, hip, knee))
    except Exception:
        return None

    torso_len = _point_distance(shoulder, hip)
    upper_leg_len = _point_distance(hip, knee)
    lower_leg_len = _point_distance(knee, ankle)
    vertical_span = float(ankle[1] - shoulder[1])

    features = np.array(
        [
            shoulder[0] - hip[0],
            shoulder[1] - hip[1],
            knee[0] - hip[0],
            knee[1] - hip[1],
            ankle[0] - hip[0],
            ankle[1] - hip[1],
            hip_angle / 180.0,
            knee_angle / 180.0,
            torso_len,
            upper_leg_len,
            lower_leg_len,
            _safe_ratio(upper_leg_len, torso_len),
            _safe_ratio(lower_leg_len, upper_leg_len),
            vertical_span,
        ],
        dtype=np.float32,
    )
    return features


class CentroidExerciseModel:
    """Nearest-centroid model persisted as JSON for easy portability."""

    def __init__(self, class_names, scaler_mean, scaler_std, centroids):
        self.class_names = list(class_names)
        self.scaler_mean = np.asarray(scaler_mean, dtype=np.float32)
        self.scaler_std = np.asarray(scaler_std, dtype=np.float32)
        self.centroids = np.asarray(centroids, dtype=np.float32)

    def predict(self, feature_vector):
        scaled = (feature_vector - self.scaler_mean) / self.scaler_std
        distances = np.linalg.norm(self.centroids - scaled, axis=1)
        logits = -2.0 * distances
        logits -= np.max(logits)
        exp_logits = np.exp(logits)
        probs = exp_logits / np.sum(exp_logits)
        best_idx = int(np.argmax(probs))
        return self.class_names[best_idx], float(probs[best_idx])

    def to_dict(self):
        return {
            "version": 1,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "class_names": self.class_names,
            "scaler_mean": self.scaler_mean.tolist(),
            "scaler_std": self.scaler_std.tolist(),
            "centroids": self.centroids.tolist(),
        }

    @classmethod
    def from_dict(cls, payload):
        return cls(
            class_names=payload["class_names"],
            scaler_mean=payload["scaler_mean"],
            scaler_std=payload["scaler_std"],
            centroids=payload["centroids"],
        )

    @classmethod
    def from_file(cls, model_path):
        with open(model_path, "r", encoding="utf-8") as fp:
            payload = json.load(fp)
        return cls.from_dict(payload)

    def save(self, model_path):
        model_dir = os.path.dirname(model_path)
        if model_dir:
            os.makedirs(model_dir, exist_ok=True)
        with open(model_path, "w", encoding="utf-8") as fp:
            json.dump(self.to_dict(), fp, indent=2)


def build_centroid_model(features_by_class):
    class_names = sorted(features_by_class)
    stacked = []
    labels = []
    for class_name in class_names:
        class_features = np.asarray(features_by_class[class_name], dtype=np.float32)
        if class_features.size == 0:
            continue
        stacked.append(class_features)
        labels.extend([class_name] * class_features.shape[0])

    if not stacked:
        raise ValueError("No training features available.")

    all_features = np.vstack(stacked)
    scaler_mean = all_features.mean(axis=0)
    scaler_std = all_features.std(axis=0)
    scaler_std = np.where(scaler_std < 1e-6, 1.0, scaler_std)
    scaled = (all_features - scaler_mean) / scaler_std

    centroids = []
    start = 0
    for class_name in class_names:
        class_count = len(features_by_class.get(class_name, []))
        if class_count == 0:
            continue
        class_slice = scaled[start : start + class_count]
        centroids.append(class_slice.mean(axis=0))
        start += class_count

    effective_class_names = [c for c in class_names if len(features_by_class.get(c, [])) > 0]
    return CentroidExerciseModel(
        class_names=effective_class_names,
        scaler_mean=scaler_mean,
        scaler_std=scaler_std,
        centroids=np.asarray(centroids, dtype=np.float32),
    )


class ExerciseClassifier:
    """Exercise classification using trained centroid model with heuristic fallback."""

    def __init__(self, model_path=DEFAULT_MODEL_PATH):
        self.model_path = model_path
        self.model = None
        self.source = "heuristic"
        self.classes = ["squat", "lunge", "plank", "standing", "unknown"]
        self._try_load_model()

    def _try_load_model(self):
        if not self.model_path or not os.path.exists(self.model_path):
            return
        try:
            self.model = CentroidExerciseModel.from_file(self.model_path)
            self.source = "model"
            self.classes = list(self.model.class_names)
            print(f"ExerciseClassifier: loaded model from {self.model_path}")
        except Exception as err:
            self.model = None
            self.source = "heuristic"
            print(f"ExerciseClassifier: failed to load model ({err})")

    def predict(self, landmarks):
        features = extract_features(landmarks)
        if features is None:
            return PredictionResult(exercise="unknown", confidence=0.0, source=self.source)

        if self.model is not None:
            exercise, confidence = self.model.predict(features)
            return PredictionResult(
                exercise=exercise, confidence=float(confidence), source="model"
            )

        exercise, confidence = self._predict_heuristic(landmarks)
        return PredictionResult(
            exercise=exercise, confidence=float(confidence), source="heuristic"
        )

    @staticmethod
    def _predict_heuristic(landmarks):
        shoulder = landmarks["shoulder"]
        hip = landmarks["hip"]
        knee = landmarks["knee"]
        ankle = landmarks["ankle"]

        knee_angle = calculate_angle(hip, knee, ankle)
        hip_angle = calculate_angle(shoulder, hip, knee)
        vertical_span = ankle[1] - shoulder[1]
        hip_to_ankle_dx = abs(ankle[0] - hip[0])

        # Side-view plank is usually flatter (smaller vertical span).
        if vertical_span < 0.25:
            return "plank", 0.72

        if knee_angle < 120 and hip_angle < 130:
            return "squat", 0.78

        # Lunge often has noticeable side displacement between hip and ankle.
        if 105 <= knee_angle <= 150 and hip_to_ankle_dx > 0.09:
            return "lunge", 0.64

        if knee_angle > 155 and hip_angle > 150:
            return "standing", 0.7

        return "unknown", 0.35
