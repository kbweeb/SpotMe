from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocketDisconnect
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "name": "GymBuddy backend",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
        "websocket": "/ws",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    
    # Create new instances per connection to avoid shared state
    pose = PoseDetector()
    squat = SquatCounter()

    while True:
        try:
            data = await ws.receive_text()
             
            # Validate and decode image data
            try:
                if data.startswith("data:") and "," in data:
                    data = data.split(",", 1)[1]
                img_bytes = base64.b64decode(data, validate=True)
                np_arr = np.frombuffer(img_bytes, np.uint8)
                frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                
                if frame is None:
                    await ws.send_json({
                        "detected": False,
                        "reps": squat.reps,
                        "feedback": "",
                        "error": "Invalid image data"
                    })
                    continue
                    
            except Exception as e:
                await ws.send_json({
                    "detected": False,
                    "reps": squat.reps,
                    "feedback": "",
                    "error": f"Failed to decode image: {str(e)}"
                })
                continue

            landmarks = pose.process(frame)
            if not landmarks:
                await ws.send_json({
                    "detected": False,
                    "reps": squat.reps,
                    "feedback": ""
                })
                continue

            reps, feedback = squat.analyze(landmarks)

            await ws.send_json({
                "detected": True,
                "reps": reps,
                "feedback": feedback or ""
            })
            
        except WebSocketDisconnect:
            break
        except Exception as e:
            print(f"WebSocket error: {e}")
            try:
                await ws.send_json({
                    "detected": False,
                    "reps": squat.reps if 'squat' in locals() else 0,
                    "feedback": "",
                    "error": str(e)
                })
            except Exception:
                break
