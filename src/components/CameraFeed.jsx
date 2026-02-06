import { useRef, useEffect } from "react";

export default function CameraFeed({ videoRef }) {
  useEffect(() => {
    async function startCamera() {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
      });
      videoRef.current.srcObject = stream;
    }
    startCamera();
  }, []);

  return (
    <video
      ref={videoRef}
      autoPlay
      playsInline
      style={{ width: "640px", height: "480px" }}
    />
  );
}
