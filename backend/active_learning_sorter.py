import argparse
import os
import shutil

import cv2

from exercise_classifier import DEFAULT_MODEL_PATH, ExerciseClassifier
from pose import PoseDetector


IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def iter_image_paths(root_dir):
    for current_root, _, files in os.walk(root_dir):
        for file_name in files:
            if file_name.lower().endswith(IMAGE_EXTENSIONS):
                yield os.path.join(current_root, file_name)


def ensure_unique_path(path):
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    idx = 1
    while True:
        candidate = f"{base}_{idx}{ext}"
        if not os.path.exists(candidate):
            return candidate
        idx += 1


def store_image(src_path, dst_dir, delete_source):
    os.makedirs(dst_dir, exist_ok=True)
    dst_path = ensure_unique_path(os.path.join(dst_dir, os.path.basename(src_path)))
    if delete_source:
        shutil.move(src_path, dst_path)
    else:
        shutil.copy2(src_path, dst_path)
    return dst_path


def main():
    parser = argparse.ArgumentParser(
        description="Sort incoming images into auto_labeled/ or needs_review/ using model confidence."
    )
    parser.add_argument(
        "--incoming-dir",
        default="incoming",
        help="Directory containing new incoming images.",
    )
    parser.add_argument(
        "--auto-labeled-dir",
        default="auto_labeled",
        help="Destination root for confident predictions.",
    )
    parser.add_argument(
        "--needs-review-dir",
        default="needs_review",
        help="Destination root for low-confidence or invalid samples.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.90,
        help="Confidence threshold for auto-labeling.",
    )
    parser.add_argument(
        "--model-path",
        default=DEFAULT_MODEL_PATH,
        help="Exercise classifier checkpoint path.",
    )
    parser.add_argument(
        "--delete-source",
        action="store_true",
        help="Move files instead of copying them.",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.incoming_dir):
        raise SystemExit(f"Incoming directory not found: {args.incoming_dir}")

    detector = PoseDetector()
    classifier = ExerciseClassifier(model_path=args.model_path)

    print(f"Pose backend: {detector.backend}")
    print(f"Classifier source: {classifier.source}")
    print(f"Threshold: {args.threshold:.2f}")

    summary = {
        "incoming": 0,
        "auto_labeled": 0,
        "needs_review": 0,
        "invalid": 0,
        "no_pose": 0,
    }

    for image_path in iter_image_paths(args.incoming_dir):
        summary["incoming"] += 1

        frame = cv2.imread(image_path)
        if frame is None:
            summary["invalid"] += 1
            store_image(
                image_path,
                os.path.join(args.needs_review_dir, "invalid_image"),
                args.delete_source,
            )
            continue

        landmarks = detector.process(frame)
        if not landmarks:
            summary["no_pose"] += 1
            summary["needs_review"] += 1
            store_image(
                image_path,
                os.path.join(args.needs_review_dir, "no_pose"),
                args.delete_source,
            )
            continue

        prediction = classifier.predict(landmarks)
        if prediction.exercise != "unknown" and prediction.confidence >= args.threshold:
            summary["auto_labeled"] += 1
            store_image(
                image_path,
                os.path.join(args.auto_labeled_dir, prediction.exercise),
                args.delete_source,
            )
            continue

        summary["needs_review"] += 1
        target_label = prediction.exercise if prediction.exercise else "unknown"
        store_image(
            image_path,
            os.path.join(args.needs_review_dir, target_label),
            args.delete_source,
        )

    print("\nSorting summary:")
    print(f"  incoming: {summary['incoming']}")
    print(f"  auto_labeled: {summary['auto_labeled']}")
    print(f"  needs_review: {summary['needs_review']}")
    print(f"  no_pose: {summary['no_pose']}")
    print(f"  invalid_image: {summary['invalid']}")


if __name__ == "__main__":
    main()
