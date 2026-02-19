import { useCallback, useState } from "react";
import CameraView from "./components/CameraView";
import "./App.css";

function App() {
  const [reps, setReps] = useState(0);
  const [feedback, setFeedback] = useState("");
  const [status, setStatus] = useState("Starting GymBuddy...");

  const speak = useCallback((text) => {
    if (!text) return;
    if (typeof window === "undefined") return;
    if (!window.speechSynthesis || !window.SpeechSynthesisUtterance) return;
    try {
      window.speechSynthesis.cancel();
      window.speechSynthesis.speak(new window.SpeechSynthesisUtterance(text));
    } catch (err) {
      console.warn("Speech synthesis failed", err);
    }
  }, []);

  const handleUpdate = useCallback(
    (data) => {
      if (data.reps !== undefined) setReps(data.reps);
      if (data.error) {
        setFeedback(data.error);
        return;
      }
      if (data.feedback) {
        setFeedback(data.feedback);
        speak(data.feedback);
      } else {
        setFeedback("");
      }
    },
    [speak],
  );

  const handleStatus = useCallback((message) => {
    setStatus(message);
  }, []);

  return (
    <div className="app">
      <h1>GymBuddy AI (Python Powered)</h1>
      <CameraView onUpdate={handleUpdate} onStatus={handleStatus} />
      <p className="status">{status}</p>
      <h2>Reps: {reps}</h2>
      <p className="feedback">{feedback || "No movement feedback yet."}</p>
    </div>
  );
}

export default App;
