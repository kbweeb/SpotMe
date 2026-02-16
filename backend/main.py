from fastapi import FastAPI, WebSocket
import cv2
import numpy as np
import base64
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pose import PoseDetector
from squat import SquatCounter

app = FastAPI()
pose = PoseDetector()
squat = SquatCounter()

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()

    while True:
        data = await ws.receive_text()
        img_bytes = base64.b64decode(data)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        landmarks = pose.process(frame)
        if not landmarks:
            await ws.send_json({"detected": False})
            continue

        reps, feedback = squat.analyze(landmarks)

        await ws.send_json({
            "detected": True,
            "reps": reps,
            "feedback": feedback
        })
