# GymBuddy Next Steps

Based on the shared guidance from `https://chatgpt.com/share/69a5e9f5-018c-800f-86b6-ad810d5b0702`, adapted to this repo.

## Implementation Status (This Repo)
- Implemented baseline exercise pipeline:
- `backend/exercise_classifier.py`
- `backend/init_dataset.py`
- `backend/collect_dataset_images.py`
- `backend/train_exercise_classifier.py`
- `backend/active_learning_sorter.py`
- `backend/main.py` now returns `exercise`, `confidence`, `classifier` in `/ws`.
- `frontend/src/App.jsx` now displays exercise + confidence + classifier source.

## 1) Expand Scope From Squat-Only
- Start with 8-12 bodyweight classes:
- `squat`, `pushup`, `lunge`, `plank`, `crunch`, `jumping_jack`, `burpee`, `mountain_climber`, `high_knees`, `glute_bridge`
- Keep current squat counter running while adding exercise classification in parallel.

## 2) Collect Data With Stable Labels
- Use folder labels first (supervised baseline):
- `dataset/train/<class_name>/...`
- `dataset/val/<class_name>/...`
- Target at least `30-50` images per class to start, then increase toward `200+` per class.
- Capture variation: people, angles, lighting, backgrounds.

## 3) Prefer Pose-Keypoint Classification
- Reuse existing pose pipeline (`backend/pose.py`) to extract normalized keypoints.
- Train a lightweight classifier on keypoints (MLP) before raw-image CNN.
- Keep image model optional; keypoints are a better fit for exercise posture.

## 4) Add Checkpoint-Based Continued Training
- First run saves `best_model.pt`.
- Later runs load checkpoint and continue training with newly added data.
- Keep class names stable between runs; if classes change, rebuild output layer and retrain.

## 5) Add Active Learning Loop
- New frames/images go to `incoming/`.
- If confidence >= threshold (ex: `0.90`), auto-label into `auto_labeled/<class>/`.
- If confidence < threshold, route to `needs_review/`.
- Periodically merge reviewed data and fine-tune from checkpoint.

## 6) Integrate Into Live App
- Backend WebSocket response should include:
- `exercise`, `confidence`, `reps`, `feedback`
- Frontend should show the detected exercise and confidence with current rep feedback.

## 7) Immediate Implementation Order
1. Add dataset structure and data collection script.
2. Add keypoint extraction + training script.
3. Add inference module to backend and include exercise label in `/ws` response.
4. Add active-learning sorter script for `incoming/`.
5. Add frontend UI fields for exercise/confidence.
