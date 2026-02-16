import cv2
import numpy as np
import os
import urllib.request

# OpenPose (COCO) model URLs commonly used
PROTO_URL = "https://raw.githubusercontent.com/opencv/opencv_extra/master/testdata/dnn/pose_deploy_linevec.prototxt"
MODEL_URL = "http://posefs1.perception.cs.cmu.edu/OpenPose/models/pose/coco/pose_iter_440000.caffemodel"

MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
PROTO_PATH = os.path.join(MODEL_DIR, "pose_deploy_linevec.prototxt")
MODEL_PATH = os.path.join(MODEL_DIR, "pose_iter_440000.caffemodel")

COCO_POINTS = {
    "nose": 0,
    "neck": 1,
    "RShoulder": 2,
    "LShoulder": 5,
    "RHip": 8,
    "LHip": 11,
    "RKnee": 9,
    "LKnee": 12,
    "RAnkle": 10,
    "LAnkle": 13,
}


def ensure_model():
    os.makedirs(MODEL_DIR, exist_ok=True)
    ok = True
    if not os.path.exists(PROTO_PATH):
        try:
            print("Downloading pose prototxt...")
            urllib.request.urlretrieve(PROTO_URL, PROTO_PATH)
        except Exception as e:
            print(f"Failed to download prototxt: {e}")
            ok = False
    if not os.path.exists(MODEL_PATH):
        try:
            print("Downloading pose caffemodel (large)...")
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        except Exception as e:
            print(f"Failed to download caffemodel: {e}")
            ok = False
    return ok


class OpenPoseDetector:
    def __init__(self, thresh=0.1):
        self.net = None
        self.thresh = thresh
        if ensure_model():
            try:
                self.net = cv2.dnn.readNetFromCaffe(PROTO_PATH, MODEL_PATH)
                print("✓ OpenPoseDetector: model loaded")
            except Exception as e:
                print(f"Error loading OpenPose model: {e}")
                self.net = None
        else:
            print("OpenPoseDetector: model not available")

    def detect(self, frame):
        """Return landmarks dict with normalized coords (x,y) for shoulder/hip/knee/ankle or None"""
        if self.net is None:
            return None

        h, w = frame.shape[:2]
        inWidth = 368
        inHeight = 368
        inp = cv2.resize(frame, (inWidth, inHeight))
        inpBlob = cv2.dnn.blobFromImage(inp, 1.0 / 255, (inWidth, inHeight), (0, 0, 0), swapRB=False, crop=False)

        self.net.setInput(inpBlob)
        output = self.net.forward()

        nPoints = output.shape[1]
        H = output.shape[2]
        W = output.shape[3]

        points = [None] * nPoints
        for i in range(nPoints):
            probMap = output[0, i, :, :]
            minVal, prob, minLoc, point = cv2.minMaxLoc(probMap)
            x = (w * point[0]) / W
            y = (h * point[1]) / H
            if prob > self.thresh:
                points[i] = (x, y, prob)
            else:
                points[i] = None

        # Build averaged landmarks
        def avg(p1, p2):
            a = points[p1] if p1 is not None else None
            b = points[p2] if p2 is not None else None
            if a and b:
                return ((a[0] + b[0]) / (2 * w), (a[1] + b[1]) / (2 * h))
            if a:
                return (a[0] / w, a[1] / h)
            if b:
                return (b[0] / w, b[1] / h)
            return None

        # Access indices safely
        def idx(name):
            return COCO_POINTS.get(name)

        shoulder = avg(idx("RShoulder"), idx("LShoulder"))
        hip = avg(idx("RHip"), idx("LHip"))
        knee = avg(idx("RKnee"), idx("LKnee"))
        ankle = avg(idx("RAnkle"), idx("LAnkle"))

        if shoulder and hip and knee and ankle:
            return {
                "shoulder": shoulder,
                "hip": hip,
                "knee": knee,
                "ankle": ankle,
            }
        return None
