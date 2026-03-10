# GymBuddy

GymBuddy is a local AI workout assistant for pose-based workout tracking.  
It uses a React frontend for camera capture and a FastAPI backend for pose detection, rep counting, and exercise classification.

## Features

- Live webcam capture in the browser.
- Real-time movement analysis over WebSocket.
- Rep counting with form feedback.
- Exercise classification with confidence scoring:
  - Trained keypoint model from checkpoint when available.
  - Heuristic classifier fallback when no checkpoint exists.
- Speech feedback in the frontend (browser speech synthesis).
- Multiple pose backends with fallback:
  - Local MoveNet (TFLite) when available.
  - MediaPipe solutions / tasks.
  - OpenPose (OpenCV DNN) fallback path.
  - Heuristic fallback if no detector backend is available.

## Tech Stack

- Frontend: React + Vite
- Backend: FastAPI + Uvicorn
- CV/AI: OpenCV, MediaPipe, NumPy

## Project Structure

```text
Gymbuddy/
  backend/
    main.py             # FastAPI app + WebSocket endpoint
    pose.py             # Pose backend selection + landmark extraction
    squat.py            # Squat rep counting logic
    exercise_classifier.py
    init_dataset.py
    collect_dataset_images.py
    train_exercise_classifier.py
    active_learning_sorter.py
    requirements.txt
  frontend/
    src/
      App.jsx
      components/CameraView.jsx
  run_project.ps1       # Starts backend + frontend in separate PowerShell windows
  run_tests.py          # Lightweight system checks
```

## Prerequisites

- Python 3.x
- Node.js + npm
- Webcam access in browser

## Setup

### 1) Install backend dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

### 2) Install frontend dependencies

```powershell
npm --prefix frontend install
```

### 3) (Optional) Install root workspace scripts

```powershell
npm install
```

This is only needed if you want to run convenience scripts from the repository root.

## Run

### Option A: Start services manually (two terminals)

Terminal 1 (backend):

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8010
```

Terminal 2 (frontend):

```powershell
npm --prefix frontend run dev
```

Then open: `http://127.0.0.1:5173`

### Option B: Start both from one command (Windows PowerShell)

```powershell
npm run dev:all
```

`run_project.ps1` opens two new PowerShell windows and starts:

- Backend: `http://127.0.0.1:8010`
- Frontend: `http://127.0.0.1:5173`

## Backend API

### `GET /`

Service metadata and endpoint list.

### `GET /health`

Basic health check:

```json
{ "status": "ok" }
```

### `WS /ws`

Real-time frame processing endpoint.

Client sends:

- Base64 JPEG frame string
- Data URL format is also accepted (`data:image/jpeg;base64,...`)

Server responses include:

```json
{
  "detected": true,
  "reps": 3,
  "feedback": "Rep 3",
  "exercise": "squat",
  "confidence": 0.93,
  "classifier": "model"
}
```

Error example:

```json
{
  "detected": false,
  "reps": 0,
  "feedback": "",
  "exercise": "unknown",
  "confidence": 0.0,
  "classifier": "heuristic",
  "error": "Invalid image data"
}
```

## Classifier Workflow

### 1) Create dataset folders

```powershell
python backend/init_dataset.py
```

### 2) Collect labeled images from webcam

```powershell
python backend/collect_dataset_images.py --label squat --split train
```

Controls: `S` save one frame, `A` toggle auto-capture, `Q` quit.

### 3) Train keypoint classifier checkpoint

```powershell
python backend/train_exercise_classifier.py --dataset-root dataset
```

This writes a checkpoint to `backend/models/exercise_classifier.json`.

### 4) Sort new incoming images with active learning

```powershell
python backend/active_learning_sorter.py --incoming-dir incoming --threshold 0.90
```

Confident predictions go to `auto_labeled/<class>/`; low confidence or no-pose images go to `needs_review/`.

## Frontend Configuration

`frontend/src/components/CameraView.jsx` supports these optional Vite env vars:

- `VITE_BACKEND_HOST` (default: current page hostname)
- `VITE_BACKEND_PORT` (default: `8010`)
- `VITE_CAMERA_FLIP_HORIZONTAL` (default: `true`)

For local overrides, create `frontend/.env`:

```env
VITE_BACKEND_HOST=127.0.0.1
VITE_BACKEND_PORT=8010
VITE_CAMERA_FLIP_HORIZONTAL=true
```

## Testing

Run the system checks:

```powershell
python run_tests.py
```

Additional quick checks:

```powershell
python test_system.py
python test_mediapipe.py
```

## Notes

- Browser camera access requires `localhost`/`127.0.0.1` or HTTPS.
- If pose detection models are missing, `PoseDetector` will try fallback backends.
- Feedback is intentionally simple and currently focused on squat depth and rep transitions.
