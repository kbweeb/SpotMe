import { useEffect, useRef } from "react";

export default function CameraView({ onUpdate }) {
  const videoRef = useRef();
  const wsRef = useRef();

  useEffect(() => {
    wsRef.current = new WebSocket("ws://localhost:8000/ws");

    navigator.mediaDevices.getUserMedia({ video: true }).then(stream => {
      videoRef.current.srcObject = stream;
    });

    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    const sendFrame = () => {
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      ctx.drawImage(videoRef.current, 0, 0);
      const base64 = canvas.toDataURL("image/jpeg").split(",")[1];
      wsRef.current.send(base64);
    };

    wsRef.current.onmessage = (msg) => {
      const data = JSON.parse(msg.data);
      onUpdate(data);
    };

    const interval = setInterval(sendFrame, 150);
    return () => clearInterval(interval);
  }, []);

  return <video ref={videoRef} autoPlay muted />;
}
