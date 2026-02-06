import { useState } from "react";
import CameraView from "./components/CameraView";
import Dashboard from "./components/DashBoard";
import { unlockAudio } from "./ai/voice";
import { startSession, endSession } from "./tracking/session";
import "./App.css";

function App() {
  const [running, setRunning] = useState(false);
  const [reps, setReps] = useState(0);
  const [session, setSession] = useState(null);
  const [duration, setDuration] = useState(0);

  const start = () => {
    unlockAudio();
    setSession(startSession());
    setRunning(true);
  };

  const stop = () => {
    const ended = endSession(session);
    setReps(reps);
    setDuration(Math.floor(ended.duration));
    setRunning(false);
  };

  return (
    <div className="app">
      <h1>GymBuddy AI 🏋🏾‍♂️</h1>

      {!running && <button onClick={start}>Start Workout</button>}
      {running && <button onClick={stop}>Stop Workout</button>}

      {running && <CameraView onRep={setReps} />}

      {!running && session && (
        <Dashboard reps={reps} duration={duration} />
      )}
    </div>
  );
}

export default App;
