import argparse
import os
import time

import cv2


def ensure_output_dir(dataset_root, split, label):
    output_dir = os.path.join(dataset_root, split, label)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def next_filename(output_dir, prefix):
    existing = [name for name in os.listdir(output_dir) if name.startswith(prefix)]
    idx = len(existing) + 1
    return os.path.join(output_dir, f"{prefix}_{idx:05d}.jpg")


def main():
    parser = argparse.ArgumentParser(
        description="Collect labeled exercise images from webcam into dataset/train|val."
    )
    parser.add_argument("--label", required=True, help="Class label, e.g. squat or pushup.")
    parser.add_argument(
        "--split",
        default="train",
        choices=["train", "val"],
        help="Dataset split to write to.",
    )
    parser.add_argument(
        "--dataset-root",
        default="dataset",
        help="Dataset root containing train/ and val/ directories.",
    )
    parser.add_argument(
        "--camera-index",
        type=int,
        default=0,
        help="Webcam index passed to OpenCV VideoCapture.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.75,
        help="Auto-capture interval in seconds when enabled.",
    )
    args = parser.parse_args()

    output_dir = ensure_output_dir(args.dataset_root, args.split, args.label)
    cap = cv2.VideoCapture(args.camera_index)
    if not cap.isOpened():
        raise SystemExit(f"Could not open camera index {args.camera_index}")

    print(f"Collecting images into: {os.path.abspath(output_dir)}")
    print("Controls: [S] save one frame, [A] toggle auto-capture, [Q] quit")

    auto_capture = False
    saved = 0
    last_save = 0.0
    prefix = f"{args.split}_{args.label}"

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                continue

            overlay = frame.copy()
            mode = "AUTO" if auto_capture else "MANUAL"
            cv2.putText(
                overlay,
                f"Label: {args.label} | Split: {args.split} | Mode: {mode} | Saved: {saved}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
            )
            cv2.imshow("GymBuddy Dataset Collector", overlay)

            now = time.time()
            if auto_capture and now - last_save >= args.interval:
                save_path = next_filename(output_dir, prefix)
                cv2.imwrite(save_path, frame)
                saved += 1
                last_save = now

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("s"):
                save_path = next_filename(output_dir, prefix)
                cv2.imwrite(save_path, frame)
                saved += 1
                last_save = now
            if key == ord("a"):
                auto_capture = not auto_capture
                last_save = now
    finally:
        cap.release()
        cv2.destroyAllWindows()

    print(f"Saved {saved} image(s) to {os.path.abspath(output_dir)}")


if __name__ == "__main__":
    main()
