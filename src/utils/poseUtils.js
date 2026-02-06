export function calculateAngle(a, b, c) {
  const radians =
    Math.atan2(c.y - b.y, c.x - b.x) -
    Math.atan2(a.y - b.y, a.x - b.x);

  let angle = Math.abs((radians * 180) / Math.PI);
  if (angle > 180) angle = 360 - angle;
  return angle;
}

export function isSquatDown(keypoints) {
  const hip = keypoints.find(k => k.name === "left_hip");
  const knee = keypoints.find(k => k.name === "left_knee");
  const ankle = keypoints.find(k => k.name === "left_ankle");

  if (!hip || !knee || !ankle) return false;

  const angle = calculateAngle(hip, knee, ankle);
  return angle < 90; // deep squat
}
