import { speak } from "./voice";

export function analyzePosture(landmarks) {
  const shoulder = landmarks[11];
  const hip = landmarks[23];
  const knee = landmarks[25];

  const backAngle = angle(shoulder, hip, knee);

  if (backAngle < 160) {
    speak("Straighten your back");
    return true;
  }

  return false;
}

function angle(a, b, c) {
  const ab = { x: a.x - b.x, y: a.y - b.y };
  const cb = { x: c.x - b.x, y: c.y - b.y };

  const dot = ab.x * cb.x + ab.y * cb.y;
  const magAB = Math.hypot(ab.x, ab.y);
  const magCB = Math.hypot(cb.x, cb.y);

  return (Math.acos(dot / (magAB * magCB)) * 180) / Math.PI;
}
