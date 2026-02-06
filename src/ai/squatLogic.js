import { speak } from "./voice";

let squatDown = false;
let reps = 0;

export function analyzeSquat(landmarks) {
  const hip = landmarks[23];
  const knee = landmarks[25];

  if (!hip || !knee) return reps;

  const depth = hip.y - knee.y;

  if (depth > 0.1 && !squatDown) {
    squatDown = true;
    speak("Good depth");
  }

  if (depth < 0.05 && squatDown) {
    squatDown = false;
    reps++;
    speak(`Rep ${reps}`);
  }

  return reps;
}
    