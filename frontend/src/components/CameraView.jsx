import { useEffect, useRef } from "react";

export default function CameraView({ onUpdate }) {
  const videoRef = useRef(null);
  const wsRef = useRef(null);

  useEffect(() => {
    let interval = null;
    let mounted = true;

    // open websocket
    try {
      wsRef.current = new WebSocket("ws://localhost:8000/ws");
      wsRef.current.onopen = () => console.log("WebSocket connected");
      wsRef.current.onclose = () => console.log("WebSocket closed");
      wsRef.current.onerror = (e) => console.warn("WebSocket error", e);
      wsRef.current.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data);
          onUpdate && onUpdate(data);
        } catch (err) {
          console.warn("Invalid WS message", err);
        }
      };
    } catch (e) {
      console.warn("Failed to create WebSocket", e);
    }

    // prepare canvas for frames
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    // get camera
    navigator.mediaDevices
      .getUserMedia({ video: true })
      .then((stream) => {
        if (!mounted) return;
        const v = videoRef.current;
        if (!v) return;
        v.srcObject = stream;
        v.playsInline = true;
        v.muted = true;
        v.autoplay = true;
        v.play().catch(() => {});

        // send frames at interval but only when video is ready
        const sendFrame = () => {
          const video = videoRef.current;
          const ws = wsRef.current;
          if (!video) return;
          const vw = video.videoWidth || video.clientWidth;
          const vh = video.videoHeight || video.clientHeight;
          if (!vw || !vh) return;
          if (!ws || ws.readyState !== WebSocket.OPEN) return;

          canvas.width = vw;
          canvas.height = vh;
          try {
            ctx.drawImage(video, 0, 0, vw, vh);
            const base64 = canvas.toDataURL("image/jpeg").split(",")[1];
            ws.send(base64);
          } catch (err) {
            console.warn("Failed to send frame", err);
          }
        };

        interval = setInterval(sendFrame, 150);
      })
      .catch((err) => {
        console.warn("getUserMedia failed:", err);
      });

    return () => {
      mounted = false;
      if (interval) clearInterval(interval);
      try {
        if (wsRef.current) wsRef.current.close();
      } catch (e) {}
      try {
        const v = videoRef.current;
        if (v && v.srcObject) {
          const tracks = v.srcObject.getTracks();
          tracks.forEach((t) => t.stop());
          v.srcObject = null;
        }
      } catch (e) {}
    };
  }, [onUpdate]);

  return <video ref={videoRef} autoPlay muted playsInline style={{ width: "100%" }} />;
}
