import argparse
import os
from collections import defaultdict

import cv2
import numpy as np

from exercise_classifier import (
    DEFAULT_MODEL_PATH,
    build_centroid_model,
    extract_features,
)
from pose import PoseDetector


IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def iter_image_paths(root_dir):
    for current_root, _, files in os.walk(root_dir):
        for file_name in files:
            if file_name.lower().endswith(IMAGE_EXTENSIONS):
                yield os.path.join(current_root, file_name)


def collect_features(split_dir, detector):
    features_by_class = defaultdict(list)
    stats = {}

    if not os.path.isdir(split_dir):
        return features_by_class, stats

    for class_name in sorted(os.listdir(split_dir)):
        class_dir = os.path.join(split_dir, class_name)
        if not os.path.isdir(class_dir):
            continue

        total = 0
        usable = 0
        for image_path in iter_image_paths(class_dir):
            total += 1
            frame = cv2.imread(image_path)
            if frame is None:
                continue
            landmarks = detector.process(frame)
            features = extract_features(landmarks)
            if features is None:
                continue
            usable += 1
            features_by_class[class_name].append(features.astype(np.float32))

        stats[class_name] = {"images": total, "usable": usable}

    return features_by_class, stats


def evaluate_model(model, features_by_class):
    total = 0
    correct = 0
    per_class = {}

    for class_name in sorted(features_by_class):
        class_features = features_by_class[class_name]
        if not class_features:
            continue
        class_total = 0
        class_correct = 0
        for feature_vector in class_features:
            pred, _ = model.predict(feature_vector)
            total += 1
            class_total += 1
            if pred == class_name:
                correct += 1
                class_correct += 1
        per_class[class_name] = (class_correct, class_total)

    accuracy = float(correct / total) if total else 0.0
    return accuracy, per_class, total


def print_split_stats(split_name, stats):
    print(f"\n[{split_name}]")
    if not stats:
        print("  No classes found.")
        return
    for class_name in sorted(stats):
        class_stats = stats[class_name]
        print(
            f"  - {class_name}: images={class_stats['images']}, "
            f"usable={class_stats['usable']}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Train a keypoint-based nearest-centroid exercise classifier."
    )
    parser.add_argument(
        "--dataset-root",
        default="dataset",
        help="Dataset root containing train/ and optional val/ subfolders.",
    )
    parser.add_argument(
        "--model-path",
        default=DEFAULT_MODEL_PATH,
        help="Where to save the classifier checkpoint JSON.",
    )
    parser.add_argument(
        "--min-samples-per-class",
        type=int,
        default=5,
        help="Minimum usable samples needed for a class to be included.",
    )
    args = parser.parse_args()

    train_dir = os.path.join(args.dataset_root, "train")
    val_dir = os.path.join(args.dataset_root, "val")

    if not os.path.isdir(train_dir):
        raise SystemExit(f"Train directory not found: {train_dir}")

    detector = PoseDetector()
    print(f"Pose backend: {detector.backend}")

    train_features, train_stats = collect_features(train_dir, detector)
    val_features, val_stats = collect_features(val_dir, detector)

    print_split_stats("train", train_stats)
    print_split_stats("val", val_stats)

    filtered_train_features = {}
    dropped_classes = []
    for class_name, class_features in train_features.items():
        if len(class_features) < args.min_samples_per_class:
            dropped_classes.append((class_name, len(class_features)))
            continue
        filtered_train_features[class_name] = class_features

    if dropped_classes:
        print("\nClasses dropped for insufficient usable samples:")
        for class_name, count in dropped_classes:
            print(
                f"  - {class_name}: {count} usable sample(s), "
                f"need >= {args.min_samples_per_class}"
            )

    if len(filtered_train_features) < 2:
        raise SystemExit(
            "Need at least two classes meeting min sample count to train classifier."
        )

    model = build_centroid_model(filtered_train_features)
    model.save(args.model_path)
    print(f"\nSaved model: {os.path.abspath(args.model_path)}")
    print(f"Classes: {', '.join(model.class_names)}")

    train_acc, train_per_class, train_total = evaluate_model(model, filtered_train_features)
    print(f"Train accuracy: {train_acc:.3f} ({train_total} sample(s))")
    for class_name in sorted(train_per_class):
        hits, count = train_per_class[class_name]
        class_acc = hits / count if count else 0.0
        print(f"  - {class_name}: {class_acc:.3f} ({hits}/{count})")

    eval_val_features = {
        class_name: features
        for class_name, features in val_features.items()
        if class_name in model.class_names
    }
    val_acc, val_per_class, val_total = evaluate_model(model, eval_val_features)
    if val_total:
        print(f"\nVal accuracy: {val_acc:.3f} ({val_total} sample(s))")
        for class_name in sorted(val_per_class):
            hits, count = val_per_class[class_name]
            class_acc = hits / count if count else 0.0
            print(f"  - {class_name}: {class_acc:.3f} ({hits}/{count})")
    else:
        print("\nVal accuracy: skipped (no usable validation features for model classes).")


if __name__ == "__main__":
    main()
