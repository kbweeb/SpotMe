import argparse
import os


DEFAULT_CLASSES = [
    "squat",
    "pushup",
    "lunge",
    "plank",
    "crunch",
    "jumping_jack",
    "burpee",
    "mountain_climber",
    "high_knees",
    "glute_bridge",
]


def ensure_layout(root_dir, class_names):
    created = []
    for split in ("train", "val"):
        for class_name in class_names:
            path = os.path.join(root_dir, split, class_name)
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                created.append(path)
    return created


def main():
    parser = argparse.ArgumentParser(
        description="Create dataset directory layout for GymBuddy exercise classifier."
    )
    parser.add_argument(
        "--dataset-root",
        default="dataset",
        help="Root directory that will contain train/ and val/ splits.",
    )
    parser.add_argument(
        "--classes",
        default=",".join(DEFAULT_CLASSES),
        help="Comma-separated class names.",
    )
    args = parser.parse_args()

    class_names = [name.strip() for name in args.classes.split(",") if name.strip()]
    if not class_names:
        raise SystemExit("No class names provided.")

    created = ensure_layout(args.dataset_root, class_names)
    print(f"Dataset root: {os.path.abspath(args.dataset_root)}")
    print(f"Classes ({len(class_names)}): {', '.join(class_names)}")
    print(f"Created directories: {len(created)}")
    for path in created:
        print(f"  - {path}")


if __name__ == "__main__":
    main()
