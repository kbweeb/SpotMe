import React, { useEffect, useRef, useState } from "react";

const FLIP_CAMERA_HORIZONTAL =
  (import.meta.env.VITE_CAMERA_FLIP_HORIZONTAL ?? "true").toLowerCase() === "true";

export default function CameraView({ onUpdate, onStatus }) {
  const videoRef = useRef(null);
  const wsRef = useRef(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraMessage, setCameraMessage] = useState(
    "Requesting camera permission (localhost/HTTPS required)...",
  );

  useEffect(() => {
    let interval = null;
    let mounted = true;
    const videoElement = videoRef.current;

    const stopResources = () => {
      if (interval) clearInterval(interval);
      setCameraActive(false);
      const ws = wsRef.current;
      if (ws) {
        try {
          ws.close();
        } catch (err) {
          console.warn("WebSocket close failed", err);
        }
      }
      if (videoElement && videoElement.srcObject) {
        try {
          const tracks = videoElement.srcObject.getTracks();
          tracks.forEach((track) => track.stop());
          videoElement.srcObject = null;
        } catch (err) {
          console.warn("Camera cleanup failed", err);
        }
      }
    };

    const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
    const backendHost =
      import.meta.env.VITE_BACKEND_HOST || window.location.hostname || "127.0.0.1";
    const backendPort = import.meta.env.VITE_BACKEND_PORT || "8010";
    const wsUrl = `${wsProtocol}://${backendHost}:${backendPort}/ws`;
    onStatus?.("Connecting to backend...");

    // open websocket
    try {
      wsRef.current = new WebSocket(wsUrl);
      wsRef.current.onopen = () => {
        console.log("WebSocket connected");
        onStatus?.("Backend connected. Requesting camera...");
      };
      wsRef.current.onclose = () => {
        console.log("WebSocket closed");
        onStatus?.("Backend disconnected. Check port 8010.");
      };
      wsRef.current.onerror = (e) => {
        console.warn("WebSocket error", e);
        onStatus?.("WebSocket error. Make sure backend is running.");
      };
      wsRef.current.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data);
          onUpdate?.(data);
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

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      const message = "Camera API unavailable. Use localhost or HTTPS.";
      onStatus?.(message);
      return () => {
        mounted = false;
        stopResources();
      };
    }

    // get camera
    navigator.mediaDevices
      .getUserMedia({ video: true })
      .then((stream) => {
        if (!mounted) return;
        if (!videoElement) {
          onStatus?.("Video element missing.");
          return;
        }
        setCameraMessage("Initializing camera stream...");
        videoElement.srcObject = stream;
        videoElement.playsInline = true;
        videoElement.muted = true;
        videoElement.autoplay = true;
        videoElement.play().then(() => {
          setCameraActive(true);
          setCameraMessage("");
          onStatus?.("Camera active.");
        }).catch(() => {
          console.warn("Video autoplay failed");
          setCameraActive(false);
          setCameraMessage("Video autoplay failed. Click the page and retry.");
          onStatus?.("Video autoplay failed. Click page and retry.");
        });

        // send frames at interval but only when video is ready
        const sendFrame = () => {
          const ws = wsRef.current;
          if (!videoElement) return;
          const vw = videoElement.videoWidth || videoElement.clientWidth;
          const vh = videoElement.videoHeight || videoElement.clientHeight;
          if (!vw || !vh) return;
          if (!ws || ws.readyState !== WebSocket.OPEN) return;

          canvas.width = vw;
          canvas.height = vh;
          try {
            if (!ctx) return;
            ctx.save();
            if (FLIP_CAMERA_HORIZONTAL) {
              ctx.translate(vw, 0);
              ctx.scale(-1, 1);
            }
            ctx.drawImage(videoElement, 0, 0, vw, vh);
            ctx.restore();
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
        setCameraActive(false);
        const errorMessage = `Camera access failed: ${err?.name || "UnknownError"}`;
        setCameraMessage(errorMessage);
        onStatus?.(errorMessage);
      });

    return () => {
      mounted = false;
      stopResources();
    };
  }, [onStatus, onUpdate]);

  return (
    <div className="camera-wrap">
      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        className={`camera-video${FLIP_CAMERA_HORIZONTAL ? " camera-video--flipped" : ""}`}
      />
      {!cameraActive && <div className="camera-overlay">{cameraMessage}</div>}
    </div>
  );
}
