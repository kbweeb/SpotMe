import { useEffect, useRef } from "react";
import { initPose } from "../ai/pose";
import { analyzeSquat } from "../ai/squatLogic";

export default function CameraView({ onRep }) {
  const videoRef = useRef();

  useEffect(() => {
    async function setupCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
        });
        videoRef.current.srcObject = stream;

        initPose(videoRef.current, (results) => {
          if (results.poseLandmarks) {
            const reps = analyzeSquat(results.poseLandmarks);
            onRep(reps);
          }
        });
      } catch (error) {
        console.error("Camera access error:", error);
      }
    }

    setupCamera();
  }, [onRep]);

  return (
    <video
      ref={videoRef}
      autoPlay
      playsInline
      muted
      style={{ width: "100%", borderRadius: "12px" }}
    />
  );
}
