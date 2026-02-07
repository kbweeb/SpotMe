import { useState } from "react";
import CameraView from "./components/CameraView";
import "./App.css";

function App() {
  const [reps, setReps] = useState(0);
  const [feedback, setFeedback] = useState("");

  const speak = (text) => {
    if (!text) return;
    speechSynthesis.cancel();
    speechSynthesis.speak(new SpeechSynthesisUtterance(text));
  };

  return (
    <div className="app">
      <h1>GymBuddy AI (Python Powered)</h1>
      <CameraView
        onUpdate={(data) => {
          if (data.reps !== undefined) setReps(data.reps);
          if (data.feedback) {
            setFeedback(data.feedback);
            speak(data.feedback);
          }
        }}
      />
      <h2>Reps: {reps}</h2>
      <p>{feedback}</p>
    </div>
  );
}

export default App;
