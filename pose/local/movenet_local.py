"""MoveNet Lightning local TFLite detector wrapper.

This module tries to use tflite-runtime or TensorFlow's Interpreter. It expects
model file at `backend/models/movenet_lightning.tflite` (relative path from repo root).

If model missing, it will print instructions and return None from `detect()`.
"""
import os
import numpy as np
import cv2

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "backend", "models", "movenet_lightning.tflite")
MODEL_PATH = os.path.normpath(MODEL_PATH)


class MoveNetLocal:
    def __init__(self):
        self.interpreter = None
        self.input_size = 192  # MoveNet Lightning
        # Try tflite-runtime first
        try:
            from tflite_runtime.interpreter import Interpreter
            self.Interpreter = Interpreter
            print("✓ MoveNetLocal: using tflite_runtime Interpreter")
        except Exception:
            try:
                from tensorflow.lite import Interpreter
                self.Interpreter = Interpreter
                print("✓ MoveNetLocal: using tensorflow.lite Interpreter")
            except Exception:
                self.Interpreter = None

        if self.Interpreter and os.path.exists(MODEL_PATH):
            try:
                self.interpreter = self.Interpreter(model_path=MODEL_PATH)
                self.interpreter.allocate_tensors()
                print(f"✓ MoveNetLocal: loaded model {MODEL_PATH}")
            except Exception as e:
                print(f"Failed to load MoveNet TFLite model: {e}")
                self.interpreter = None
        else:
            if not os.path.exists(MODEL_PATH):
                print("MoveNet model not found.")
                print("Download the model and place it at:")
                print(MODEL_PATH)
                print("Download URL (manual): https://tfhub.dev/google/lite-model/movenet/singlepose/lightning/4?lite-format=tflite")

    def _preprocess(self, frame):
        img = np.copy(frame)
        img = cv2.resize(img, (self.input_size, self.input_size))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img.astype(np.float32)
        img = img / 255.0
        img = img[np.newaxis, ...]
        return img

    def detect(self, frame):
        if self.interpreter is None:
            return None
        input_data = self._preprocess(frame)
        input_details = self.interpreter.get_input_details()
        output_details = self.interpreter.get_output_details()
        self.interpreter.set_tensor(input_details[0]['index'], input_data)
        self.interpreter.invoke()
        output_data = self.interpreter.get_tensor(output_details[0]['index'])
        # output_data shape: (1,1,17,3) or (1,17,3)
        arr = output_data.squeeze()
        if arr.ndim == 3:
            arr = arr[0]
        # Map MoveNet keypoint indices to standard names
        keypoint_names = [
            'nose','left_eye','right_eye','left_ear','right_ear',
            'left_shoulder','right_shoulder','left_elbow','right_elbow',
            'left_wrist','right_wrist','left_hip','right_hip',
            'left_knee','right_knee','left_ankle','right_ankle'
        ]
        out = {}
        for i, name in enumerate(keypoint_names):
            y, x, score = arr[i]
            out[name] = [float(x), float(y), float(score)]
        return out
