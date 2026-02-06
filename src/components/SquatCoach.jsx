import * as poseDetection from "@tensorflow-models/pose-detection";
import "@tensorflow/tfjs";
import { useEffect, useRef, useState } from "react";
import { isSquatDown } from "../utils/poseUtils";
import { speak } from "../utils/speech";
import CameraFeed from "./CameraFeed";

export default function SquatCoach() {
  const videoRef = useRef(null);
  const [reps, setReps] = useState(0);
  const squatState = useRef("up");

  useEffect(() => {
    let detector;
    let animationId;

    async function loadModel() {
      detector = await poseDetection.createDetector(
        poseDetection.SupportedModels.MoveNet
      );

      detect(detector);
    }

    async function detect(detector) {
      if (videoRef.current && videoRef.current.readyState === 4) {
        const poses = await detector.estimatePoses(videoRef.current);
        if (poses.length > 0) {
          const keypoints = poses[0].keypoints;

          if (isSquatDown(keypoints) && squatState.current === "up") {
            squatState.current = "down";
            speak("Good depth");
          }

          if (!isSquatDown(keypoints) && squatState.current === "down") {
            squatState.current = "up";
            setReps(r => r + 1);
            speak("One rep");
          }
        }
      }
      animationId = requestAnimationFrame(() => detect(detector));
    }

    loadModel();

    return () => {
      if (animationId) cancelAnimationFrame(animationId);
      if (detector) detector.dispose();
    };
  }, []);

  return (
    <div>
      <CameraFeed videoRef={videoRef} />
      <h2>Reps: {reps}</h2>
    </div>
  );
}
