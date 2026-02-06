import { useRef, useEffect } from "react";

export default function CameraFeed({ videoRef }) {
  useEffect(() => {
    async function startCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
        });
        videoRef.current.srcObject = stream;
      } catch (error) {
        console.error("Camera access denied:", error);
      }
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
